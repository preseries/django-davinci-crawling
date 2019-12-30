# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.

import argparse

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

    args = parser.parse_args()

    storage_client = get_storage_client()
    print("Stopping cluster for %s" % args.username)
    try:
        bucket = storage_client.get_bucket("analyst_platform")
    except GoogleAPIError:
        bucket = storage_client.create_bucket("analyst_platform")
        pass

    hashed_name = hash_resource_name(args.username)

    # TODO: delete files from Google Storage
    # for file_name in ["datalab-cluster-init.sh"]:
    #    upload_file(storage_client, bucket,
    #                "%s/%s" % (os.path.join(os.path.dirname(__file__)),
    #                           file_name),
    #                "%s/%s" % (hashed_name, file_name))

    # Stop a datalab cluster
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

    if cluster_name:
        delete_cluster(dataproc=dataproc_client,
                       project=args.project_name,
                       region=args.region,
                       cluster_name=cluster_name)
        print("Cluster STOPPED!! you can now open your browser.")
    else:
        print("No Cluster was found for the user %s." % args.username)
