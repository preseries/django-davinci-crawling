# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging
import re
import ntpath

from davinci_crawling.io import copy_file, get_extension, exists, delete_all, \
    extract_zip, listdir, mkdirs
from davinci_crawling.net import fetch_file, fetch_tenaciously
from davinci_crawling.throttle.memory_throttle import MemoryThrottle

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from davinci_crawling.example.bovespa.models import BovespaCompanyFile
from davinci_crawling.example.bovespa.io import \
    _doc_base_path, _doc_local_base_path, _doc_local_working_base_path

try:
    from dse.cqlengine.query import LWTException
except ImportError:
    from cassandra.cqlengine.query import LWTException

RE_FILE_BY_ITR = r"^.*\.ITR"
RE_FILE_BY_DFP = r"^.*\.DFP"
RE_FILE_BY_XML = r"^.*\.XML"

_logger = logging.getLogger(
    "davinci_crawler_{}.crawling_part.download_file".
    format(BOVESPA_CRAWLER))


def extract_files_to_process(options, company_file):
    """Extract the files from the ENER zip file and the ITR/DFP inside of it,
    and collect all the XML files
    """
    force_download = options.get("force_download", False)

    local_base_path = _doc_local_base_path(options, company_file)

    # Make sure the file is in the local cache
    local_file = "{0}/{1}". \
        format(local_base_path, company_file.file_name)
    if not exists(options, local_file):
        copy_file(options, company_file.file_url, local_file)

    working_local_base_path = \
        _doc_local_working_base_path(options, company_file)
    file_to_export = "{0}/{1}".format(local_base_path, company_file.file_name)

    if exists(options, working_local_base_path):
        if force_download:
            # Clean the folder of the company file (working folder)
            delete_all(options, working_local_base_path)
            files_ref = extract_zip(
                options, file_to_export, working_local_base_path)
        else:
            files_ref = listdir(options, working_local_base_path)
            # If the folder is empty
            if not files_ref:
                mkdirs(options, working_local_base_path)
                files_ref = extract_zip(
                    options, file_to_export, working_local_base_path)
    else:
        mkdirs(options, working_local_base_path)
        files_ref = extract_zip(
            options, file_to_export, working_local_base_path)

    available_files = {}

    if company_file.doc_type in ["ITR", "DFP"]:
        for the_file in files_ref:
            if re.match(RE_FILE_BY_XML, the_file, re.IGNORECASE):
                filename = ntpath.basename(the_file)
                available_files[filename] = the_file
            elif re.match(RE_FILE_BY_ITR, the_file, re.IGNORECASE):
                itr_dest_folder = "{0}/itr_content/".\
                    format(working_local_base_path)
                itr_files = extract_zip(options, the_file, itr_dest_folder)
                for itr_file in itr_files:
                    filename = ntpath.basename(itr_file)
                    available_files["itr/{}".format(filename)] = itr_file
                # Once unzipped, we can delete the original file from the
            elif re.match(RE_FILE_BY_DFP, the_file, re.IGNORECASE):
                dfp_dest_folder = "{0}/dfp_content/".\
                    format(working_local_base_path)
                dfp_files = extract_zip(options, the_file, dfp_dest_folder)
                for dfp_file in dfp_files:
                    filename = ntpath.basename(dfp_file)
                    available_files["dfp/{}".format(filename)] = dfp_file

    return local_file, working_local_base_path, available_files


@MemoryThrottle(crawler_name=BOVESPA_CRAWLER, minutes=1, rate=50,
                max_tokens=50)
def download_file(options, ccvm, doc_type, fiscal_date, version):
    company_file = BovespaCompanyFile.objects.get(
        ccvm=ccvm,
        doc_type=doc_type,
        fiscal_date=fiscal_date,
        version=version)

    # Build the path and file name
    local_base_path = _doc_local_base_path(options, company_file)
    cache_base_path = _doc_base_path(options, company_file)

    force_download = options.get("force_download", False)

    if force_download or \
            not company_file.file_url or \
            not exists(options, company_file.file_url):

        fetch_file_params = {
            "base_path": local_base_path
        }
        fetch_file_params.update(options)

        file = fetch_tenaciously(
            fetcher=fetch_file,
            url=company_file.source_url,
            n=10,
            s=10,
            data=fetch_file_params)

        file_url = "{0}/{1}".format(cache_base_path, file.filename)

        # Let's cache the file into our permanent storage
        copy_file(options, file.file, file_url)

        company_file.update(
            file_url=file_url,
            file_name=file.filename,
            file_extension=get_extension(file.file))

    return extract_files_to_process(options, company_file)
