# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
import copy

import logging
from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.entity_diff.diff import make_diff

_logger = logging.getLogger("davinci_crawling.testing")


class TestDiff(CaravaggioBaseTest):
    """
    Test the proxy mesh logic, this test requires connection with internet
    because we use the proxy mesh api.
    """

    all_files_count = 0
    original_json = None

    @classmethod
    def setUpTestData(cls):
        cls.original_json = {
            "list_strings": ["abc", "def"],
            "list_objects": [
                {"uuid": "f8626a86-a9ca-4b3c-958b-5f2c71442a3c", "name": "John", "age": 24, "country": "Brazil"},
                {"uuid": "b0652153-000d-4100-85e5-1d25c7793542", "name": "Mary", "age": 31, "country": "USA"},
            ],
        }

    def _compare_diff(self, original_json, modified_json, expected, should_fail=False):
        """
        Call the diff using the original and the modified json and compare with
        the expected.
        Args:
            original_json: the original json
            modified_json: the modified version that will be compared with the
                original
            expected: the expected result of the diff
        """
        result = make_diff(original_json, modified_json)

        if expected:
            result["inserts"] = sorted(result["inserts"])
            expected["inserts"] = sorted(expected["inserts"])
            result["updates"] = sorted(result["updates"])
            expected["updates"] = sorted(expected["updates"])
            result["deletes"] = sorted(result["deletes"])
            expected["deletes"] = sorted(expected["deletes"])

        try:
            self.assertDictEqual(expected, result)
        except AssertionError as e:
            if not should_fail:
                raise e

    def test_simple_list_insert(self):
        modified_json = copy.deepcopy(self.original_json)
        # insert on first position
        modified_json["list_strings"].insert(0, "new_string")

        expected = {
            "all": {"inserts": {"list_strings[0]": {"new_value": "new_string"}}},
            "inserts": ["list_strings*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

        modified_json = copy.deepcopy(self.original_json)
        # insert on the second position
        modified_json["list_strings"].insert(1, "new_string")

        expected = {
            "all": {"inserts": {"list_strings[1]": {"new_value": "new_string"}}},
            "inserts": ["list_strings*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

        modified_json = copy.deepcopy(self.original_json)
        # insert on the first position same value
        modified_json["list_strings"].insert(0, "abc")

        expected = {
            "all": {"inserts": {"list_strings[0]": {"new_value": "abc"}}},
            "inserts": ["list_strings*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_object_list_update(self):
        modified_json = copy.deepcopy(self.original_json)
        # invert the order of the elements
        modified_json["list_objects"][0], modified_json["list_objects"][1] = (
            modified_json["list_objects"][1],
            modified_json["list_objects"][0],
        )

        expected = {"all": {}, "inserts": [], "updates": [], "deletes": []}

        # this should fail because we are not in the same order on the two
        # dictionaries
        self._compare_diff(self.original_json, modified_json, expected, should_fail=True)

        sorted_current = sorted(self.original_json["list_objects"], key=lambda i: i["uuid"])
        sorted_previous = sorted(modified_json["list_objects"], key=lambda i: i["uuid"])

        self._compare_diff(sorted_current, sorted_previous, expected)

    def test_object_list_update_many(self):
        original_json = {"many": [{"uuid": 1}, {"uuid": 2}]}
        modified_json = {"many": [{"uuid": 2}, {"uuid": 1}]}

        expected = {
            "all": {
                "updates": {
                    "many[0].uuid": {"new_value": 2, "old_value": 1},
                    "many[1].uuid": {"new_value": 1, "old_value": 2},
                }
            },
            "inserts": [],
            "updates": ["many*"],
            "deletes": [],
        }

        # this should fail because we are not in the same order on the two
        # dictionaries
        self._compare_diff(original_json, modified_json, expected)
