#!/bin/bash

# Use the metadata server to get the configuration specified during
# instance creation. Read more about metadata here:
# https://cloud.google.com/compute/docs/metadata#querying
function get_parameter() {
    CODE="$(curl -sS -o /dev/null -s -w "%{http_code}\n" http://metadata/computeMetadata/v1/instance/attributes/$1 -H "Metadata-Flavor: Google")"

    if [ "$CODE" != "200" ]
    then
        echo "$2"
    else
        echo "$(curl -sS http://metadata/computeMetadata/v1/instance/attributes/$1 -H "Metadata-Flavor: Google")"
    fi
}

CRAWLER_IMAGE=$(get_parameter "crawler-image" "")
CRAWLER_NAME=$(get_parameter "crawler-name" "")
WORKERS_NUM=$(get_parameter "--workers-num" "5")
VERBOSE_LEVEL=$(get_parameter "--verbose-level" "0")
CACHE_DIR=$(get_parameter "--cache-dir" "gs://davinci_cache")
LOCAL_DIR=$(get_parameter "--local-dir" "fs:///data/harvest/local")

# [START startup_script]
apt-get update

PARAMETERS=$(curl http://metadata/computeMetadata/v1/instance/attributes/parameters -H "Metadata-Flavor: Google")

ENV_VARS=$(curl http://metadata/computeMetadata/v1/instance/attributes/environment-vars -H "Metadata-Flavor: Google")


#if [ -z "$WORKERS_NUM" ]
#then
#      WORKERS_NUM=5
#      exit 2
#fi

echo "Crawler Startup" > details.txt
echo "Crawler image: $CRAWLER_IMAGE" > details.txt
echo "Crawler name: $CRAWLER_NAME" >> details.txt
echo "Workers num: $WORKERS_NUM" >> details.txt
echo "Verbose: $VERBOSE_LEVEL" >> details.txt
echo "Cache dir: $CACHE_DIR" >> details.txt
echo "Local dir: $LOCAL_DIR" >> details.txt
echo "Custom parameters: $PARAMETERS" >> details.txt
echo "Environment variales: $ENV_VARS" >> details.txt

# Create the Google Cloud Storage bucket if it does not exists.
# gsutil mb $CACHE_DIR

# python manage.py crawl bovespa \
#    -v 0 --workers-num 10 \
#    --phantomjs-path /phantomjs-2.1.1-macosx/bin/phantomjs \
#    --io-gs-project centering-badge-212119 \
#    --cache-dir "gs://vanggogh2_harvest" \
#    --local-dir "fs:///data/harvest/local"

# Start the crawler using the Docker image

{ # try
    echo "docker run -d --entrypoint docker-crawl-entrypoint.sh $ENV_VARS --name $CRAWLER_NAME $CRAWLER_IMAGE -v $VERBOSE_LEVEL --workers-num $WORKERS_NUM --phantomjs-path /usr/local/bin/phantomjs --cache-dir "$CACHE_DIR" --local-dir "$LOCAL_DIR" $PARAMETERS" >> details.txt
    # docker run -ti --name crawler busybox /bin/sh
    docker run -d --entrypoint docker-crawl-entrypoint.sh $ENV_VARS --name $CRAWLER_NAME $CRAWLER_IMAGE -v $VERBOSE_LEVEL --workers-num $WORKERS_NUM --phantomjs-path /usr/local/bin/phantomjs --cache-dir "$CACHE_DIR" --local-dir "$LOCAL_DIR" $PARAMETERS
    docker wait crawler &&
    # gcloud compute instances delete $CRAWLER_NAME
    #save your output
} || { # catch
    # save log for exception
    gcloud compute instances delete $CRAWLER_NAME
}

# [END startup_script]