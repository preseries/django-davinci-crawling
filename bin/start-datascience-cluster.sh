#!/bin/bash

function usage {
    echo "usage: $0 username team"
    echo " "
    echo "Username format 'xalperte' 35"
    exit 1
}

if [ $# -ne 2 ]; then
    usage
fi

username=$1
team=$2

python start-datascience-cluster.py \
    --username $username \
    --team $team \
    --type jupiter \
    --project-name bgds-prod \
    --region us-east1 \
    --zone us-east1-b \
    --master-type n1-standard-1 \
    --worker-type n1-standard-1 \
    --worker-instances 2