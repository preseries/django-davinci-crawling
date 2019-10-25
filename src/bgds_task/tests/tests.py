# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import os
import json
import logging
import time
import math

from datetime import datetime, timedelta
from dateutil import relativedelta

from caravaggio_rest_api.utils import delete_all_records
from bgds_task.models import Bgds_taskResource

from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User

from caravaggio_rest_api.utils import default

from caravaggio_rest_api.tests import CaravaggioBaseTest

# Create your tests here.
from bgds_task.api.serializers import \
    Bgds_taskResourceSerializerV1, \
    Bgds_taskResourceSearchSerializerV1, \
    Bgds_taskResourceGEOSearchSerializerV1, \
    Bgds_taskResourceFacetSerializerV1

CONTENTTYPE_JON = "application/json"

_logger = logging.getLogger()


class GetAllTest(CaravaggioBaseTest):
    """ Test module for bgds_taskResource model """
    resources = []

    persisted_resources = []

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

        # We clean the test database (bgds_taskResource)
        delete_all_records(Bgds_taskResource)

        # We load the test data from the data.json file using the
        # serializer class
        current_path = os.path.dirname(os.path.abspath(__file__))
        cls.resources = GetAllTest.\
            load_test_data("{}/data.json".format(current_path),
                           Bgds_taskResourceSerializerV1)

    def step1_create_resources(self):
        for resource in self.resources:
            _logger.info("POST Resource: {}".format(resource["name"]))
            response = self.api_client.post(reverse("bgds_task-list"),
                                            data=json.dumps(
                                                resource, default=default),
                                            content_type=CONTENTTYPE_JON)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.persisted_resources.append(response.data["_id"])

        _logger.info("Persisted resources: {}".
                     format(self.persisted_resources))

        # We need to wait until the data has been indexed (Cassandra-Solr)
        # We need to give time for the next search tests
        time.sleep(0.5)

    def step2_get_resources(self):
        for index, resource_id in enumerate(self.persisted_resources):
            original_resource = self.resources[index]
            path = "{0}{1}/".format(reverse("bgds_task-list"), resource_id)
            _logger.info("Path: {}".format(path))
            response = self.api_client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data["name"], original_resource["name"])
            super(GetAllTest, self).assert_equal_dicts(
                response.data, original_resource,
                ["_id", "created_at", "updated_at"])

    def step3_search_text(self):
        """
        We search any resource that contains a text in the text field, that is
        a field that concentrates all the textual fields
        (corpus of the resource)
        """
        path = "{0}?text=distributed".format(reverse("bgds_task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        # BigML (position 2)
        self.assertEqual(
            response.data["results"][0]["name"], self.resources[1]["name"])
        super(GetAllTest, self).assert_equal_dicts(
            response.data["results"][0], self.resources[1],
            ["_id", "created_at", "updated_at", "score"])

    def step4_search_specialties(self):
        """"
        Get resources that have "Internet" in their specialties.

        And get resources that have specialties that contains "*Internet*"
        in their name but do not have "Hardware"
        """
        path = "{0}?specialties=Internet".\
            format(reverse("bgds_task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)

        # Get resources that contains *Internet* in their specialties
        # but do not contains "Hardware"
        path = "{0}?specialties__contains=Internet&" \
               "specialties__not=Hardware".\
            format(reverse("bgds_task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        # BigML (position 2)
        self.assertEqual(
            response.data["results"][0]["name"], self.resources[1]["name"])
        super(GetAllTest, self).assert_equal_dicts(
            response.data["results"][0], self.resources[1],
            ["_id", "created_at", "updated_at", "score"])

    def step5_search_geo(self):
        """"
        Will get all the resources within 10 km from the point
             with longitude -123.25022 and latitude 44.59641.
        """
        path = "{0}?km=10&from=44.59641,-123.25022".\
            format(reverse("bgds_task-geosearch-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["results"][0]["name"], self.resources[1]["name"])
        super(GetAllTest, self).assert_equal_dicts(
            response.data["results"][0], self.resources[1],
            ["_id", "created_at", "updated_at", "score"])

    def step6_search_facets(self):
        """"
        Will get all the faces for the existent resources
        """
        path = "{0}facets/?country_code=limit:1".\
            format(reverse("bgds_task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["fields"]["country_code"]), 1)
        self.assertEqual(response.data[
            "fields"]["country_code"][0]["text"], "USA")
        self.assertEqual(response.data[
            "fields"]["country_code"][0]["count"], 2)

        self.assertEqual(len(response.data["fields"]["crawl_param"]), 2)
        self.assertEqual(response.data[
            "fields"]["crawl_param"][0]["text"], '1')
        self.assertEqual(response.data[
            "fields"]["crawl_param"][0]["count"], 1)
        self.assertEqual(response.data[
            "fields"]["crawl_param"][1]["text"], '2')
        self.assertEqual(response.data[
            "fields"]["crawl_param"][1]["count"], 1)

        self.assertEqual(len(response.data["fields"]["specialties"]), 5)
        self.assertEqual(response.data[
            "fields"]["specialties"][0]["text"], "Internet")
        self.assertEqual(response.data[
            "fields"]["specialties"][0]["count"], 2)
        self.assertEqual(response.data[
            "fields"]["specialties"][1]["text"], "Hardware")
        self.assertEqual(response.data[
            "fields"]["specialties"][1]["count"], 1)
        self.assertEqual(response.data[
            "fields"]["specialties"][2]["text"], "Machine Learning")
        self.assertEqual(response.data[
            "fields"]["specialties"][2]["count"], 1)
        self.assertEqual(response.data[
            "fields"]["specialties"][3]["text"], "Predictive Analytics")
        self.assertEqual(response.data[
            "fields"]["specialties"][3]["count"], 1)
        self.assertEqual(response.data[
            "fields"]["specialties"][4]["text"], "Telecommunications")
        self.assertEqual(response.data[
            "fields"]["specialties"][4]["count"], 1)

        start_date = datetime.now() - timedelta(days=50 * 365)
        end_date = datetime.now()
        r = relativedelta.relativedelta(end_date, start_date)
        expected_buckets = math.ceil((r.years * 12 + r.months) / 6)

        self.assertIn(len(response.data["dates"]["foundation_date"]),
                      [expected_buckets, expected_buckets + 1])

        def get_date_bucket_text(start_date, bucket_num, months_bw_buckets):
            return (start_date + relativedelta.relativedelta(
                months=+bucket_num * months_bw_buckets)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0).strftime(
                "%Y-%m-%dT%H:%M:%SZ")

        self.assertEqual(
            response.data["dates"]["foundation_date"][52]["text"],
            get_date_bucket_text(start_date, 52, 6))
        self.assertEqual(
            response.data["dates"]["foundation_date"][84]["text"],
            get_date_bucket_text(start_date, 84, 6))

    def step7_search_facets_ranges(self):
        """"
        Let's change the foundation_date facet range by all the years from
        1st Jan 2010 til today. Total: 8 years/buckets
        """
        path = "{0}facets/?" \
               "foundation_date=start_date:20th May 2010," \
               "end_date:10th Jun 2015,gap_by:year,gap_amount:1".\
            format(reverse("bgds_task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["dates"]["foundation_date"]), 6)

        buckets = {bucket["text"]: bucket["count"]
                   for bucket in response.data["dates"]["foundation_date"]}

        self.assertTrue("2011-01-01T00:00:00Z" in buckets)
        self.assertEqual(buckets["2011-01-01T00:00:00Z"], 1)

    def step8_search_facets_narrow(self):
        """"
        Drill down when selection facets
        """
        path = "{0}facets/?selected_facets=specialties_exact:Hardware&" \
               "selected_facets=country_code_exact:USA".\
            format(reverse("bgds_task-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["fields"]["country_code"]), 1)
        self.assertEqual(response.data[
            "fields"]["country_code"][0]["text"], "USA")
        self.assertEqual(response.data[
            "fields"]["country_code"][0]["count"], 1)

        self.assertEqual(len(response.data["fields"]["specialties"]), 5)

        specialties = {specialty["text"]: specialty["count"]
                       for specialty in response.data["fields"]["specialties"]}

        self.assertTrue("Hardware" in specialties)
        self.assertEqual(specialties["Hardware"], 1)

        self.assertTrue("Internet" in specialties)
        self.assertEqual(specialties["Internet"], 1)

        self.assertTrue("Machine Learning" in specialties)
        self.assertEqual(specialties["Machine Learning"], 0)

        self.assertTrue("Predictive Analytics" in specialties)
        self.assertEqual(specialties["Predictive Analytics"], 0)

        self.assertTrue("Telecommunications" in specialties)
        self.assertEqual(specialties["Telecommunications"], 1)
