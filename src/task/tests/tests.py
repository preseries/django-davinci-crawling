# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import os
import json
import logging
import time

from caravaggio_rest_api.utils import delete_all_records
from task.models import Task

from rest_framework import status
from django.urls import reverse

from caravaggio_rest_api.utils import default

from caravaggio_rest_api.tests import CaravaggioBaseTest

# Create your tests here.
from task.api.serializers import \
    TaskSerializerV1

CONTENTTYPE_JSON = "application/json"

_logger = logging.getLogger()


class GetAllTest(CaravaggioBaseTest):
    """ Test module for Task model """
    resources = []

    persisted_resources = []

    post_resources = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Let's create some extra users to use as owners of the data

        # This user represents a crawler user (automatic user)
        cls.crunchbase = cls.create_user(
            email="crunchbase@harvester.com",
            first_name="CrunchBase",
            last_name="Crawler")

        # This user represents a human user
        cls.manual_user_1 = cls.create_user(
            email="user@mycompany.com",
            first_name="Jorge",
            last_name="Clooney")

        # We clean the test database (Task)
        delete_all_records(Task)

        # We load the test data from the data.json file using the
        # serializer class
        current_path = os.path.dirname(os.path.abspath(__file__))
        cls.resources = GetAllTest.\
            load_test_data("{}/data.json".format(current_path),
                           TaskSerializerV1)

    def step1_create_resources(self):
        for resource in self.resources:
            _logger.info("POST Resource: {}".format(resource["kind"]))
            response = self.api_client.post(reverse("task-list"),
                                            data=json.dumps(
                                                resource, default=default),
                                            content_type=CONTENTTYPE_JSON)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            task_id = response.data["task_id"]
            self.persisted_resources.append(task_id)
            self.post_resources.append(response.data)

        _logger.info("Persisted resources: {}".
                     format(self.persisted_resources))

        # We need to wait until the data has been indexed (Cassandra-Solr)
        # We need to give time for the next search tests
        time.sleep(1)

    def step1_invalid_data(self):
        invalid_resources = [
            {
                # missing required field params
                "kind": "bovespa"
            },
            {
                # missing required field kind
                "params": {
                    "workers_num": 20
                }
            }
        ]

        for resource in invalid_resources:
            response = self.api_client.post(reverse("task-list"),
                                            data=json.dumps(
                                                resource, default=default),
                                            content_type=CONTENTTYPE_JSON)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def step2_get_resources(self):
        for index, resource_id in enumerate(self.persisted_resources):
            original_resource = self.post_resources[index]
            path = "{0}{1}/".format(reverse("task-list"), resource_id)
            _logger.info("Path: {}".format(path))
            response = self.api_client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data["task_id"], original_resource["task_id"])
            super(GetAllTest, self).assert_equal_dicts(
                response.data, original_resource,
                ["task_id", "created_at", "updated_at"])

    def step3_search_kind(self):
        """
        We search any resource that contains a text in the text field, that is
        a field that concentrates all the textual fields
        (corpus of the resource)
        """
        path = "{0}?kind=bovespa".format(reverse("task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)
        # BigML (position 2)

        for index, result in enumerate(response.data["results"]):
            super(GetAllTest, self).assert_equal_dicts(
                result, self.post_resources[index],
                ["task_id", "created_at", "updated_at", "kind"])

    def step4_search_params(self):
        """"
        Get resources that have "Internet" in their specialties.

        And get resources that have specialties that contains "*Internet*"
        in their name but do not have "Hardware"
        """
        path = "{0}?status=0".\
            format(reverse("task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 3)
        # Get resources that contains *Internet* in their specialties
        # but do not contains "Hardware"
        path = "{0}?status=1".\
            format(reverse("task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 0)

    def step5_search_facets(self):
        """"
        Will get all the faces for the existent resources
        """
        path = "{0}facets/?kind=limit:2".\
            format(reverse("task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["fields"]["kind"]), 2)
        self.assertEqual(response.data[
            "fields"]["kind"][0]["text"], "bovespa")
        self.assertEqual(response.data[
            "fields"]["kind"][0]["count"], 2)
        self.assertEqual(response.data[
            "fields"]["kind"][1]["text"], "web")
        self.assertEqual(response.data[
            "fields"]["kind"][1]["count"], 1)

        self.assertEqual(len(response.data["fields"]["status"]), 1)
        self.assertEqual(response.data[
            "fields"]["status"][0]["text"], '0')
        self.assertEqual(response.data[
            "fields"]["status"][0]["count"], 3)

        self.assertEqual(len(response.data["fields"]["type"]), 1)
        self.assertEqual(response.data[
            "fields"]["type"][0]["text"], '1')
        self.assertEqual(response.data[
            "fields"]["type"][0]["count"], 3)

    def step6_put_not_allowed(self):
        for resource in self.post_resources:
            _logger.info("DELETE Resource: {}".format(resource["task_id"]))
            response = self.api_client.put(reverse("task-list"),
                                           data=json.dumps(
                                               resource, default=default),
                                           content_type=CONTENTTYPE_JSON)
            self.assertEqual(response.status_code,
                             status.HTTP_405_METHOD_NOT_ALLOWED)

    def step7_patch_not_allowed(self):
        for resource in self.post_resources:
            _logger.info("Patch Resource: {}".format(resource["task_id"]))
            response = self.api_client.patch(reverse("task-list"),
                                             data=json.dumps(
                                                 resource, default=default),
                                             content_type=CONTENTTYPE_JSON)
            self.assertEqual(response.status_code,
                             status.HTTP_405_METHOD_NOT_ALLOWED)

    def step8_delete_on_by_one(self):
        for resource in self.post_resources:
            resource_id = resource["task_id"]
            _logger.info("Delete Resource: {}".format(resource_id))
            path = "{0}{1}/".format(reverse("task-list"),
                                    resource_id)
            response = self.api_client.delete(path)
            self.assertEqual(response.status_code,
                             status.HTTP_204_NO_CONTENT)

            path = "{0}{1}/".format(reverse("task-list"), resource_id)
            _logger.info("Path: {}".format(path))
            response = self.api_client.get(path)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
