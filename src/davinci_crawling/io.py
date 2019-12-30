# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import pathlib
import logging
import datetime
import os
import re
import shutil
import tempfile
import zipfile

from spitslurp import spit, slurp

try:
    from dse.cqlengine.query import DoesNotExist
except ImportError:
    from cassandra.cqlengine.query import DoesNotExist

from google.cloud import storage
# Imports the Google Cloud client libraries
from google.api_core.exceptions import GoogleAPIError

from davinci_crawling.models import Checkpoint

BACKEND_RE = r'(.*)://.*'
BUCKET_NAME_RE = r'gs:\/\/(\w+)\/?.*$'
BUCKET_PATH_RE = r'gs:\/\/\w+\/?(.*)$'
FILE_EXTENSION_RE = r'^.*\.(.*)$'
FILE_PATH_RE = r'fs://(.*)'

_logger = logging.getLogger("davinci_crawling")


def get_backend(path):
    try:
        return re.match(BACKEND_RE, path)[1]
    except TypeError:
        msg = "Invalid backend: {}".format(path)
        _logger.exception(msg)
        raise Exception(msg)


def get_gs_bucket_name(options):
    cache_dir = options.get("cache_dir", None)
    try:
        return re.match(BUCKET_NAME_RE, cache_dir)[1]
    except TypeError as ex:
        msg = "Unable to get the bucket name " \
              "from the cache_dir OPTION: {}".format(cache_dir)
        _logger.exception(msg)
        raise Exception(msg)


def get_gs_path(path):
    try:
        return re.match(BUCKET_PATH_RE, path)[1]
    except TypeError as ex:
        msg = "Unable to get the path from the GSPath: {}".format(path)
        _logger.exception(msg)
        raise Exception(msg)


def get_gs_client(options):
    io_gs_project = options.get("io_gs_project", None)
    if io_gs_project:
        storage_client = storage.Client(project=io_gs_project)
    else:
        storage_client = storage.Client()

    return storage_client


def create_gs_folder(options, path):
    storage_client = get_gs_client(options)

    bucket_name = get_gs_bucket_name(options)
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob("%s_$folder$" % path)
    return blob.path


def upload_gs_file(options, source_file, dest_file, chunk_size=None):
    storage_client = get_gs_client(options)

    bucket_name = get_gs_bucket_name(options)
    bucket = storage_client.get_bucket(bucket_name)

    dest_file = get_gs_path(dest_file)

    _logger.debug(("Upload file [%s] into [gs://%s/%s]" %
                   (source_file, bucket.name, dest_file)))

    blob = bucket.blob(dest_file, chunk_size=chunk_size)
    blob.upload_from_filename(source_file)

    return blob.path


def download_gs_file(options, source_file, dest_file):
    """
    Download a file from the GCP Storage service and save the file
    into the dest_file

    Example:

    download_gs_file(options,
        "gs://vanggogh2_harvest/bovespa/ccvm_9512/ITR/00951220110331301.zip",
        "fs:///data/00951220110331301.zip")

    download_gs_file(options,
        "gs://vanggogh2_harvest/bovespa/ccvm_9512/ITR/00951220110331301.zip",
        "/data/00951220110331301.zip")
    """
    storage_client = get_gs_client(options)

    bucket_name = get_gs_bucket_name(options)
    bucket = storage_client.get_bucket(bucket_name)

    source_file_path = get_gs_path(source_file)

    blob = bucket.blob(source_file_path)

    os.makedirs(os.path.dirname(dest_file), exist_ok=True)

    try:
        file_path = re.match(FILE_PATH_RE, dest_file)[1]
    except Exception as ex:
        file_path = dest_file

    blob.download_to_filename(file_path)

    _logger.debug('Blob {} downloaded to {}.'.format(
        source_file,
        dest_file))

    return dest_file


def get_base_dir(options):
    """
    Return the control directory suitable for storing metadata
    about a running crawler. The directory will be created if it
    does not already exist.
    """
    crawler_name = options.get("crawler", None)
    cache_dir = options.get("cache_dir", None)
    backend = get_backend(cache_dir)

    _logger.debug("Output dir: {}".format(cache_dir))
    _logger.debug("Backend: {}".format(backend))

    if backend == "fs":
        file_path = re.match(FILE_PATH_RE, cache_dir)[1]
        local_path = pathlib.Path(file_path, crawler_name)
        if not local_path.exists():
            _logger.info("Local control dir doesn't exits. Creating it...")
            local_path.mkdir(parents=True, exist_ok=True)
            _logger.info("Local control dir %s successfully created." %
                         local_path.absolute())

        output_dir = str(local_path.absolute())
        _logger.debug("Output dir: {}".format(output_dir))
        return "fs://%s" % output_dir
    elif backend == "gs":
        storage_client = get_gs_client(options)
        bucket_name = re.match(BUCKET_NAME_RE, cache_dir)[1]
        _logger.debug("Bucket name: {}".format(bucket_name))
        try:
            bucket = storage_client.get_bucket(bucket_name)
        except GoogleAPIError:
            _logger.info("Bucket {} not found. Creating it...".
                         format(bucket_name))
            bucket = storage_client.create_bucket(bucket_name)
            _logger.info("Bucket {} successfully created.".
                         format(bucket_name))

        output_dir = "{0}/{1}".format(cache_dir, crawler_name)
        _logger.debug("Output dir: {}".format(output_dir))
        return output_dir
    else:
        raise NotImplemented("Unsupported backend")


def get_local_base_dir(options):
    return options.get("local_dir", None)


def get_extension(file):
    return re.match(FILE_EXTENSION_RE, file)[1]


def mkdirs(options, dest_file):
    backend = get_backend(dest_file)

    if backend == "fs":
        file_path = re.match(FILE_PATH_RE, dest_file)[1]
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    elif backend == "gs":
        # In GS the paths are created automatically when we
        # copy/upload the file
        create_gs_folder(options, dest_file)


def get_backend_and_path(options, file, raise_exceptions=False):
    try:
        backend = get_backend(file)
    except Exception as ex:
        if not raise_exceptions:
            # Using FS by default
            backend = "fs"
            pass
        else:
            _logger.exception("Unable to determine the backend"
                              " of the folder. Using FS by default.")
            raise ex

    if backend == "fs":
        try:
            return backend, re.match(FILE_PATH_RE, file)[1]
        except TypeError:
            if not raise_exceptions:
                return backend, file
            raise Exception("Invalid file path: {}".format(file))
    elif backend == "gs":
        bucket_name = get_gs_bucket_name(options)
        return backend, "{0}/{1}".format(bucket_name, get_gs_path(file))


def extract_zip(options, source_file, dest_folder, force=False):
    _logger.debug("EXTRACT ZIP: Source file: {}".format(source_file))
    _logger.debug("EXTRACT ZIP: Dest folder: {}".format(dest_folder))

    # Extract the content of the file in the cache into the working folder
    src_backend, file_to_export = get_backend_and_path(options, source_file)
    backend, clean_dest_folder = get_backend_and_path(options, dest_folder)

    _logger.debug("EXTRACT ZIP: Source backend: {}".
                  format(src_backend))
    _logger.debug("EXTRACT ZIP: Source file to export: {}".
                  format(file_to_export))
    _logger.debug("EXTRACT ZIP: Destination backend: {}".
                  format(backend))
    _logger.debug("EXTRACT ZIP: Destination folder: {}".
                  format(clean_dest_folder))

    files_ref = []

    if backend == "fs":
        # Only extract if we are force to do it or if there is not files
        # already exported before
        if force or not pathlib.Path(clean_dest_folder).exists() or \
                not os.listdir(clean_dest_folder):
            with zipfile.ZipFile(file_to_export, "r") as zip_ref:
                zip_ref.extractall(clean_dest_folder)

        for the_file in os.listdir(clean_dest_folder):
            files_ref.append(os.path.join(clean_dest_folder, the_file))

    return files_ref


def listdir(options, source_folder):
    # Extract the content of the file in the cache into the working folder
    _logger.debug("Source Folder: {}".format(source_folder))
    backend, clean_source_folder = get_backend_and_path(options, source_folder)

    _logger.debug("Backend: {}".format(backend))

    files_ref = []

    if backend == "fs":
        for the_file in os.listdir(clean_source_folder):
            files_ref.append(os.path.join(clean_source_folder, the_file))
    elif backend == "gs":
        storage_client = get_gs_client(options)
        bucket_name = get_gs_bucket_name(options)
        dest_file = get_gs_path(source_folder)
        for blob in storage_client.list_blobs(bucket_name, prefix=dest_file):
            files_ref.append(f"gs://{bucket_name}/{blob.name}")

    return files_ref


def exists(options, dest_file):
    backend = get_backend(dest_file)

    if backend == "fs":
        file_path = re.match(FILE_PATH_RE, dest_file)[1]
        return pathlib.Path(file_path).exists()
    elif backend == "gs":
        # In GS the paths are created automatically when we
        # copy/upload the file
        storage_client = get_gs_client(options)

        bucket_name = get_gs_bucket_name(options)
        bucket = storage_client.get_bucket(bucket_name)

        dest_file = get_gs_path(dest_file)
        _logger.debug(("Checking existence of file [%s] into [gs://%s]" %
                       (dest_file, bucket.name)))

        blob = bucket.blob(dest_file)
        return blob.exists()


def delete_all(options, path):
    try:
        backend = get_backend(path)
    except Exception as ex:
        _logger.exception("Unable to determine the backend"
                          " of the folder. Using FS by default.")
        backend = "fs"

    if backend == "fs":
        try:
            clean_path = re.match(FILE_PATH_RE, path)[1]
        except TypeError:
            clean_path = path

        if os.path.isfile(clean_path):
            try:
                os.unlink(clean_path)
            except Exception as e:
                raise Exception(
                    "Unable to delete the file [{0}]. "
                    "Clean version: [{1}]".format(path, clean_path))
        else:
            for the_file in os.listdir(clean_path):
                file_path = os.path.join(clean_path, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    else:
                        shutil.rmtree(file_path)
                except Exception as e:
                    raise Exception(
                        "Unable to delete the files in folder [{0}]. "
                        "Clean version: [{1}]".format(path, clean_path))


def copy_file(options, source_file, dest_file, chunk_size=None):
    with tempfile.TemporaryDirectory() as temp_path:
        # If the backend if FS in source_file we have the reference to the
        # local FS file
        source_backend, source_file = \
            get_backend_and_path(options, source_file)
        if source_backend == "gs":
            source_file = download_gs_file(
                options, "gs://{}".format(source_file),
                "fs://{0}/{1}".format(temp_path, "test.zip"))
            try:
                source_file = re.match(FILE_PATH_RE, source_file)[1]
            except TypeError:
                raise Exception("Invalid file path: {}".format(source_file))

        # If the backend if FS in file_path we have the reference to the
        # local FS file
        dest_backend, file_path = get_backend_and_path(options, dest_file)
        if dest_backend == "fs":
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            shutil.copyfile(source_file, file_path)
            return file_path
        elif dest_backend == "gs":
            # In GS the paths are created automatically when we
            # copy/upload the file
            upload_gs_file(options, source_file, dest_file,
                           chunk_size=chunk_size)

            return dest_file


def get_control_dir(options):
    return "{}/ctl".format(get_base_dir(options))


def put_control_timestamp(
        config, control_file_name="crawl-timestamp.txt",
        custom_timestamp=datetime.datetime.utcnow().isoformat()):
    control_dir = get_control_dir(config)

    backend = get_backend(control_dir)

    if backend == "fs":
        filename = "{}/{}".format(control_dir, control_file_name)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        spit(filename, custom_timestamp)


def get_control_timestamp(options,
                          control_file_name="crawl-timestamp.txt"):
    control_dir = get_control_dir(options)

    backend = get_backend(control_dir)

    if backend == "fs":
        try:
            filename = "{}/{}".format(control_dir, control_file_name)
            return slurp(filename)
        except FileNotFoundError as ex:
            return None


def get_checkpoint_data(source, key, default=None):
    try:
        return Checkpoint.objects.filter(source=source, key=key).get(). \
            get_data()
    except DoesNotExist:
        return default


def put_checkpoint_data(source, key, json_data):
    checkpoint = Checkpoint(source=source, key=key)
    checkpoint.set_data(json_data)
    checkpoint.save()
    return checkpoint
