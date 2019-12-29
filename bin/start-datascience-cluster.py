# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.

import argparse
import os

from .utils import *

# Imports the Google Cloud client libraries
from google.api_core.exceptions import GoogleAPIError


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run a Datalab Cluster in Dataproc')
    parser.add_argument('--username',
                        type=str,
                        required=True,
                        default=None,
                        dest='username',
                        help="The name of the user starting the cluster"
                             "(ex: --username xalperte)")
    parser.add_argument('--team',
                        type=int,
                        required=True,
                        default=None,
                        dest='team',
                        help="The id of the team where the user belongs"
                             "(ex: --team 450)")
    parser.add_argument('--project-name',
                        type=str,
                        required=True,
                        dest='project_name',
                        help="The GCP project used to run the jobs"
                             "(ex: --project-name bgds-prod)")
    parser.add_argument('--region',
                        type=str,
                        required=False,
                        default='us-east1',
                        dest='region',
                        help="The GCP region where provision the cluster"
                             "(ex: --region us-east1)")
    parser.add_argument('--zone',
                        type=str,
                        required=False,
                        default='us-east1-b',
                        dest='zone',
                        help="The GCP zone where provision the cluster"
                             "(ex: --zone us-east1-b)")
    parser.add_argument('--type',
                        type=str,
                        required=False,
                        default='jupiter',
                        choices=['jupiter', 'datalab'],
                        dest='cluster_type',
                        help="The data science cluster type"
                             "(ex: --type jupiter)")
    parser.add_argument('--master-type',
                        type=str,
                        required=False,
                        default='n1-standard-1',
                        choices=INSTANCES_TYPE,
                        dest='master_type',
                        help="The instance type for the spark master"
                             "(ex: --master-type n1-standard-1)")
    parser.add_argument('--worker-type',
                        type=str,
                        required=False,
                        default='n1-standard-2',
                        choices=INSTANCES_TYPE,
                        dest='worker_type',
                        help="The instance type for the spark workers"
                             "(ex: --worker-type n1-standard-2)")
    parser.add_argument('--worker-instances',
                        type=int,
                        required=False,
                        default=2,
                        dest='worker_instances',
                        help="The number of worker instances"
                             "(ex: --worker-instances 2)")

    args = parser.parse_args()

    storage_client = get_storage_client()
    print("Starting cluster for %s" % args.username)
    try:
        bucket = storage_client.get_bucket("analyst_platform")
    except GoogleAPIError:
        bucket = storage_client.create_bucket("analyst_platform")
        pass

    hashed_name = hash_resource_name(args.username)

    # Start a datalab cluster
    dataproc_client = get_dataproc_client()
    clusters = list_clusters(dataproc=dataproc_client,
                             project=args.project_name,
                             region=args.region)

    cluster_name = None

    if 'clusters' in clusters:
        cluster_list = clusters['clusters']
        for cluster in cluster_list:
            print("{} - {}"
                  .format(cluster['clusterName'], cluster['status']['state']))
            if cluster['clusterName'] == hashed_name:
                cluster_name = hashed_name
                break

    if not cluster_name:
        cluster_name = hashed_name

        # Initialization file
        if args.cluster_type == 'datalab':
            for file_name in ["datalab-cluster-init.sh"]:
                upload_file(storage_client, bucket, "./%s" % file_name,
                            "%s/%s" % (hashed_name, file_name))

            # Cluster initialization script
            init_actions = ["gs://%s/%s/datalab-cluster-init.sh" %
                            (bucket.name, hashed_name)]

            metadata = None
            properties = None
        elif args.cluster_type == 'jupiter':
            for file_name in ["jupiter-cluster-init.sh"]:
                upload_file(storage_client, bucket, "./%s" % file_name,
                            "%s/%s" % (hashed_name, file_name))

            # Cluster initialization script
            init_actions = ["gs://%s/%s/jupiter-cluster-init.sh" %
                            (bucket.name, hashed_name)]

            metadata = {
                'JUPYTER_PORT': "8124",
                # 'dataproc_bucket': "team_%d" % args.team,
                'JUPYTER_CONDA_PACKAGES': 'numpy:pandas:scikit-learn',
            }

            properties = {
                'spark:spark.executorEnv.PYTHONHASHSEED':
                    hash_resource_name('BGDSSeed_201232167312AASSXS22310'),
                'spark:spark.yarn.am.memory': '2048m',
            }
        else:
            raise Exception("Unrecognized cluster type. Valid options are: "
                            "jupiter or datalab")

        cluster = create_cluster(dataproc=dataproc_client,
                                 project=args.project_name,
                                 region=args.region,
                                 cluster_name=cluster_name,
                                 zone=args.zone,
                                 master_type=args.master_type,
                                 worker_type=args.worker_type,
                                 worker_instances=args.worker_instances,
                                 init_actions=init_actions,
                                 metadata=metadata,
                                 properties=properties)

    # Wait until the cluster is running and ready to admit jobs
    wait_for_cluster(dataproc=dataproc_client,
                     project=args.project_name,
                     region=args.region,
                     cluster_name=cluster_name)

    print("Cluster READY!! you can now open your browser.")

    print("SSH tunneling: [gcloud compute ssh %s-m --project=%s "
          "--zone=%s -- -D 8080 -N -n]" %
          (cluster_name, args.project_name, args.zone))

    print("Start browser using SOCKS (Mac OS X): "
          "[/Applications/Google Chrome.app/Contents/MacOS/Google Chrome "
          "--proxy-server=\"socks5://localhost:8080\"  "
          "--host-resolver-rules=\"MAP * 0.0.0.0, EXCLUDE localhost\"  "
          "--user-data-dir=/tmp/%s]" % args.username)

    print("Start browser using SOCKS (Linux): "
          "[/usr/bin/google-chrome "
          "--proxy-server=\"socks5://localhost:8080\"  "
          "--host-resolver-rules=\"MAP * 0.0.0.0, EXCLUDE localhost\"  "
          "--user-data-dir=/tmp/%s]" % args.username)

    print("Start browser using SOCKS (Windows): "
          "[C:/Program Files (x86)/Google/Chrome/Application/chrome.exe "
          "--proxy-server=\"socks5://localhost:8080\"  "
          "--host-resolver-rules=\"MAP * 0.0.0.0, EXCLUDE localhost\"  "
          "--user-data-dir=/tmp/%s]" % args.username)
