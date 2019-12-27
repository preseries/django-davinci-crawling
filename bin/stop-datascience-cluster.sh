#!/bin/bash

function usage {
    echo "usage: $0 username"
    echo " "
    echo "Username format 'xalperte'"
    exit 1
}

if [ $# -ne 1 ]; then
    usage
fi

username=$1

python stop-datascience-cluster.py \
    --username $username \
    --project-name bgds-prod \
    --region us-east1