# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
import time
import hashlib
import json

# Imports the Google Cloud client libraries
from google.cloud import storage
from googleapiclient import discovery

INSTANCES_TYPE = [
    "n1-standard-1",
    "n1-standard-2",
    "n1-standard-4",
    "n1-standard-8",
    "n1-standard-16",
    "n1-standard-32",
    "n1-standard-64",
    "n1-standard-96",
    "n1-highmem-2",
    "n1-highmem-4",
    "n1-highmem-8",
    "n1-highmem-16",
    "n1-highmem-32",
    "n1-highmem-64",
    "n1-highmem-96",
    "n1-highcpu-2",
    "n1-highcpu-4",
    "n1-highcpu-8",
    "n1-highcpu-16",
    "n1-highcpu-32",
    "n1-highcpu-64",
    "n1-highcpu-96",
]

INSTANCE_RESOURCES = {
    "n1-standard-1": ("3g", "1"),
    "n1-standard-2": ("5444m", "2"),
    "n1-standard-4": ("13g", "4"),
    "n1-standard-8": ("25g", "8"),
    "n1-standard-16": ("55g", "16"),
    "n1-standard-32": ("110g", "32"),
    "n1-standard-64": ("230g", "64"),
    "n1-standard-96": ("340g", "96"),
    "n1-highmem-2": ("10g", "2"),
    "n1-highmem-4": ("22g", "4"),
    "n1-highmem-8": ("48g", "8"),
    "n1-highmem-16": ("95g", "16"),
    "n1-highmem-32": ("200g", "32"),
    "n1-highmem-64": ("400g", "64"),
    "n1-highmem-96": ("610g", "96"),
    "n1-highcpu-2": ("1g", "2"),
    "n1-highcpu-4": ("2.5g", "4"),
    "n1-highcpu-8": ("6g", "8"),
    "n1-highcpu-16": ("12g", "16"),
    "n1-highcpu-32": ("25g", "32"),
    "n1-highcpu-64": ("50g", "64"),
    "n1-highcpu-96": ("90g", "96"),
}


def hash_resource_name(job_name):
    # the resource names in dataproc should start with letters
    return "a%.49s" % hashlib.sha256(job_name.encode()).hexdigest()


def get_storage_client():
    """Builds a client to the storage API."""
    storage_client = storage.Client()
    return storage_client


def create_bucket(storage_client, bucket_name):
    # Creates the new bucket
    bucket = storage_client.create_bucket(bucket_name)
    return bucket


def create_folder(storage_client, bucket, folder_name):
    if isinstance(bucket, str):
        bucket = storage_client.get_bucket(bucket)

    blob = bucket.blob("%s_$folder$" % folder_name)
    return blob


def upload_file(storage_client, bucket, file_path, file_name):
    if isinstance(bucket, str):
        bucket = storage_client.get_bucket(bucket)

    print("Upload file [%s] into [gc://%s/%s]" % (file_path, bucket.name, file_name))

    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_path)


def get_dataproc_client():
    """Builds a client to the dataproc API."""
    dataproc = discovery.build("dataproc", "v1")
    return dataproc


def list_clusters(dataproc, project, region):
    result = dataproc.projects().regions().clusters().list(projectId=project, region=region).execute()
    return result


def list_clusters_with_details(dataproc, project, region):
    result = dataproc.projects().regions().clusters().list(projectId=project, region=region).execute()
    return result


def create_cluster(
    dataproc,
    project,
    zone,
    region,
    cluster_name,
    master_type="n1-standard-1",
    worker_type="n1-standard-2",
    worker_instances=2,
    init_actions=None,
    metadata=None,
    properties=None,
):
    print("Creating cluster [%s]..." % cluster_name)
    zone_uri = "https://www.googleapis.com/compute/v1/projects/{}/zones/{}".format(project, zone)

    cluster_data = {
        "projectId": project,
        "clusterName": cluster_name,
        "config": {
            "gceClusterConfig": {"zoneUri": zone_uri},
            "masterConfig": {"numInstances": 1, "machineTypeUri": master_type},
            "workerConfig": {"numInstances": worker_instances, "machineTypeUri": worker_type},
            "softwareConfig": {},
        },
    }

    if init_actions and len(init_actions) > 0:
        cluster_data["config"]["initializationActions"] = [{"executableFile": file_name for file_name in init_actions}]

    if metadata and len(metadata) > 0:
        cluster_data["config"]["gceClusterConfig"]["metadata"] = {key: value for key, value in metadata.items()}

    if properties and len(properties) > 0:
        cluster_data["config"]["softwareConfig"]["properties"] = {key: value for key, value in properties.items()}

    print("Cluster JSON:")
    print(json.dumps(cluster_data, sort_keys=True, indent=4))

    result = (
        dataproc.projects().regions().clusters().create(projectId=project, region=region, body=cluster_data).execute()
    )

    return result


def wait_for_cluster(dataproc, project, region, cluster_name):
    print("Waiting for cluster [%s] to be provisioned..." % cluster_name)
    while True:
        result = (
            dataproc.projects()
            .regions()
            .clusters()
            .get(projectId=project, region=region, clusterName=cluster_name)
            .execute()
        )
        # Handle exceptions
        if result["status"]["state"] == "ERROR":
            raise Exception(result["status"]["details"])
        elif result["status"]["state"] == "RUNNING":
            print("Cluster ready.")
            return result


def submit_pyspark_job(
    dataproc, project, region, job_details, master_type="n1-standard-1", worker_type="n1-standard-2"
):
    """Submits the Pyspark job to the cluster, assuming `filename` has
    already been uploaded to `bucket_name`"""

    master_memory = INSTANCE_RESOURCES[master_type][0]
    master_num_of_cores = INSTANCE_RESOURCES[master_type][1]

    worker_memory = INSTANCE_RESOURCES[worker_type][0]
    worker_num_of_cores = INSTANCE_RESOURCES[worker_type][1]

    # https://github.com/hail-is/hail/issues/1186
    if "spark.driver.memory" not in job_details["job"]["pysparkJob"]["properties"]:
        job_details["job"]["pysparkJob"]["properties"]["spark.driver.memory"] = master_memory

    if "spark.driver.cores" not in job_details["job"]["pysparkJob"]["properties"]:
        job_details["job"]["pysparkJob"]["properties"]["spark.driver.cores"] = master_num_of_cores

    if "spark.executor.memory" not in job_details["job"]["pysparkJob"]["properties"]:
        job_details["job"]["pysparkJob"]["properties"]["spark.executor.memory"] = worker_memory

    if "spark.executor.cores" not in job_details["job"]["pysparkJob"]["properties"]:
        job_details["job"]["pysparkJob"]["properties"]["spark.executor.cores"] = worker_num_of_cores

    result = dataproc.projects().regions().jobs().submit(projectId=project, region=region, body=job_details).execute()
    job_id = result["reference"]["jobId"]
    print("Submitted job ID {}".format(job_id))
    return job_id


def wait_for_job(dataproc, project, region, job_id):
    print("Waiting for job [%s] to finish..." % job_id)
    while True:
        result = dataproc.projects().regions().jobs().get(projectId=project, region=region, jobId=job_id).execute()
        # Handle exceptions
        if result["status"]["state"] == "ERROR":
            raise Exception(result["status"]["details"])
        elif result["status"]["state"] == "DONE":
            print("Job finished.")
            return result

        # Wait 30 seconds
        time.sleep(30)


def delete_cluster(dataproc, project, region, cluster_name):
    print("Tearing down cluster [%s]" % cluster_name)
    result = (
        dataproc.projects()
        .regions()
        .clusters()
        .delete(projectId=project, region=region, clusterName=cluster_name)
        .execute()
    )
    return result
