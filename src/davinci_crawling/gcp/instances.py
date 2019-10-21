# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
import os
import time
import json
import logging
import googleapiclient.discovery
from jsonpath import jsonpath

from davinci_crawling.crawler import get_configuration

_logger = logging.getLogger("davinci_crawling.gcp")

DEFAULT_CONFIG = {
    "project": None,
    "zone": "europe-west2-a",

    # A list of available machine types:
    # https://cloud.google.com/compute/docs/machine-types
    "machine-type": "n1-standard-1",

    # Container - Optimized OS
    # https://cloud.google.com/compute/docs/images?hl=es-419#os-compute-support
    "image": {
        "project": "cos-cloud",
        "family": "cos-stable"
    }
}


class GCPComputeService(object):

    instance = None

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    def __init__(self) -> None:
        super().__init__()

        self.compute = googleapiclient.discovery.build('compute', 'v1')

    def commission_instance(
            self,
            crawler_image,
            crawler_name,
            current_date,
            verbosity,
            workers_num,
            cache_dir,
            local_dir,
            crawler_params,
            environment_vars):
        """
        This function is responsible for the start (commissioning) of an
        instance in GCP and run a crawler.

        :param crawler_image: the url to the docker image in GCP.
                For instance: "eu.gcr.io/project_name/
                               appengine/sky.v2018-09-hotfix-2"
        :param crawler_name: the name of the crawler to run
        :param crawler_params: the parameters to be sent to the crawler when
                we start it
        :return: the result of the operation
        """

        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug("Commission GCP instance with following detail")
            _logger.debug("\tCrawler image: {}".format(crawler_image))
            _logger.debug("\tCrawler name: {}".format(crawler_name))
            _logger.debug("\tCurrent date: {}".format(current_date))
            _logger.debug("\tVerbosity: {}".format(verbosity))
            _logger.debug("\tWorkers num: {}".format(workers_num))
            _logger.debug("\tCache dir: {}".format(cache_dir))
            _logger.debug("\tLocal dir: {}".format(local_dir))
            _logger.debug("\tCrawler params: {}".format(crawler_params))
            _logger.debug("\tEnvironment vars: {}".format(environment_vars))

        project = self._get_config_param(crawler_name, "deployment.project")[0]
        zone = self._get_config_param(crawler_name, "deployment.zone")[0]
        machine_type = \
            self._get_config_param(crawler_name, "deployment.machine-type")[0]

        image_project = \
            self._get_config_param(crawler_name, "deployment.image.project")[0]
        image_family = \
            self._get_config_param(crawler_name, "deployment.image.family")[0]

        # Get a reference to the image
        image_response = self.compute.images().getFromFamily(
            project=image_project,
            family=image_family).execute()
        source_disk_image = image_response['selfLink']

        # Configure the machine
        machine_type = "zones/{}/machineTypes/{}".format(zone, machine_type)
        startup_script = open(
            os.path.join(
                os.path.dirname(__file__), 'startup-script.sh'), 'r').read()

        paramaters = [
            "{} {}".format(key, val) for key, val in crawler_params.items()]

        variables = [
            "-e {}={}".format(key, val)
            for key, val in environment_vars.items()]

        items = [{
                # Startup script is automatically executed by the
                # instance upon startup.
                'key': 'startup-script',
                'value': startup_script
            }, {
                'key': 'crawler-image',
                'value': crawler_image
            }, {
                'key': 'crawler-name',
                'value': crawler_name
            }, {
                'key': '--current-date',
                'value': current_date
            }, {
                'key': '--verbosity',
                'value': verbosity
            }, {
                'key': '--workers-num',
                'value': workers_num
            }, {
                'key': '--cache-dir',
                'value': cache_dir
            }, {
                'key': '--local-dir',
                'value': local_dir
            }, {
                'key': 'parameters',
                'value': " ".join(paramaters)
            }, {
                'key': 'environment-vars',
                'value': " ".join(variables)
            }]

        _logger.debug("Metadata Items: {}".format(json.dumps(items, indent=4)))

        config = {
            'name': crawler_name,
            'machineType': machine_type,

            # Specify the boot disk and the image to use as a source.
            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': source_disk_image,
                    }
                }
            ],

            # Specify a network interface with NAT to access the public
            # internet.
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],

            # Allow the instance to access cloud storage and logging.
            'serviceAccounts': [{
                'email': 'default',
                'scopes': [
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    'https://www.googleapis.com/auth/logging.write'
                ]
            }],

            # Metadata is readable from the instance and allows you to
            # pass configuration from deployment scripts to instances.
            'metadata': {
                'items': items
            }
        }

        _logger.debug("Entire instance config details: {}".
                      format(json.dumps(config, indent=4)))

        return self.compute.instances().insert(
            project=project,
            zone=zone,
            body=config).execute()

    def decommission_instance(self, crawler_name):
        project = self._get_config_param(crawler_name, "deployment.project")[0]
        zone = self._get_config_param(crawler_name, "deployment.zone")[0]

        return self.compute.instances().delete(
            project=project,
            zone=zone,
            instance=crawler_name).execute()

    def wait_for_operation(self, crawler_name):
        print('Waiting for operation to finish...')

        project = self._get_config_param(crawler_name, "deployment.project")[0]
        zone = self._get_config_param(crawler_name, "deployment.zone")[0]

        while True:
            result = self.compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=crawler_name).execute()

            if result['status'] == 'DONE':
                print("done.")
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(1)

    # [END wait_for_operation]
    @classmethod
    def _get_config_param(cls, crawler_name, param):
        crawler_config = get_configuration(crawler_name)
        return jsonpath(crawler_config, param) \
            if jsonpath(crawler_config, param) else \
            jsonpath(DEFAULT_CONFIG[param], param)
