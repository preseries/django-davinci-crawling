# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
import string

import random

import copy

import json

import os

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
        current_path = os.path.dirname(os.path.abspath(__file__))
        with open("{}/data.json".format(current_path)) as json_file:
            cls.original_json = json.load(json_file)[0]

        cls.maxDiff = None

    def _compare_diff(self, original_json, modified_json, expected):
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

        self.assertDictEqual(expected, result)

    def test_non_modified(self):
        modified_json = copy.deepcopy(self.original_json)

        expected = {"all": {}, "inserts": [], "updates": [], "deletes": []}

        self._compare_diff(self.original_json, modified_json, expected)

    def test_insert_value(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["long_description"] = "A very very long description"

        expected = {
            "all": {"inserts": {"long_description": {"new_value": "A very very long description"}}},
            "inserts": ["long_description"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_update_value(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["name"] = "Open Exchange"

        expected = {
            "all": {"updates": {"name": {"new_value": "Open Exchange", "old_value": "BGDS"}}},
            "inserts": [],
            "updates": ["name"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_delete_value(self):
        modified_json = copy.deepcopy(self.original_json)
        # lets try changing to None first
        modified_json["name"] = None

        expected = {
            "all": {"updates": {"name": {"new_value": None, "old_value": "BGDS"}}},
            "inserts": [],
            "updates": ["name"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

        # now lets try deleting the key from the dict
        del modified_json["name"]

        expected = {
            "all": {"deletes": {"name": {"old_value": "BGDS"}}},
            "inserts": [],
            "updates": [],
            "deletes": ["name"],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_one_insert_value(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["headquarters"]["street_3"] = "Level 3"

        expected = {
            "all": {"inserts": {"headquarters.street_3": {"new_value": "Level 3"}}},
            "inserts": ["headquarters*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_one_insert_object(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["official_headquarters"] = {
            "address_id": "305cbe5f-3770-4780-b1d2-3bb0a4e8249b",
            "name": "headquarters",
            "street_1": "35th Jefferson street",
            "street_2": None,
            "city": "Austin",
            "region": "Texas",
            "country": "United States",
            "country_code": "USA",
            "postal_code": "11211",
            "latitude": 11221.00,
            "longitude": 11.51,
            "created_date": "2019-10-10T00:00:00Z",
            "updated_date": "2019-10-10T00:00:00Z",
        }

        expected = {
            "all": {"inserts": {"official_headquarters": {"new_value": modified_json["official_headquarters"]}}},
            "inserts": ["official_headquarters"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_one_update(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["headquarters"]["name"] = "BGDS Headquarters"

        expected = {
            "all": {"updates": {"headquarters.name": {"old_value": "headquarters", "new_value": "BGDS Headquarters"}}},
            "inserts": [],
            "updates": ["headquarters*"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_one_delete(self):
        modified_json = copy.deepcopy(self.original_json)
        # test modifying the value to None
        modified_json["headquarters"]["country_code"] = None

        expected = {
            "all": {"updates": {"headquarters.country_code": {"old_value": "USA", "new_value": None}}},
            "inserts": [],
            "updates": ["headquarters*"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)
        # test deleting the key
        del modified_json["headquarters"]["country_code"]

        expected = {
            "all": {"deletes": {"headquarters.country_code": {"old_value": "USA"}}},
            "inserts": [],
            "updates": [],
            "deletes": ["headquarters*"],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_many_insert_value(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["featured_team"][0]["name"] = "John"

        expected = {
            "all": {"inserts": {"featured_team[0].name": {"new_value": "John"}}},
            "inserts": ["featured_team*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_many_insert_object(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["featured_team"].append(
            {"job_id": "55b229c1-3cbf-46c3-a2a9-0b5966fd99b2", "title": "Software Developer"}
        )

        expected = {
            "all": {"inserts": {"featured_team[1]": {"new_value": modified_json["featured_team"][1]}}},
            "inserts": ["featured_team*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_many_update(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["featured_team"][0]["ended_on"] = "2019-31-12"

        expected = {
            "all": {"updates": {"featured_team[0].ended_on": {"new_value": "2019-31-12", "old_value": None}}},
            "inserts": [],
            "updates": ["featured_team*"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_many_delete_object(self):
        modified_json = copy.deepcopy(self.original_json)
        del modified_json["websites"][1]

        expected = {
            "all": {
                "deletes": {
                    "websites[1]": {
                        "old_value": {
                            "website_id": "3574182e-74bb-4c21-8d81-4f6091fedc12",
                            "name": "facebook",
                            "website_type": "facebook",
                            "url": "www.facebook.com/john",
                            "created_date": "2019-10-10T00:00:00Z",
                            "updated_date": "2019-10-10T00:00:00Z",
                        }
                    }
                }
            },
            "inserts": [],
            "updates": [],
            "deletes": ["websites*"],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_one_to_many_delete_value(self):
        modified_json = copy.deepcopy(self.original_json)
        # first change to None
        modified_json["funds"][0]["money_raised"] = None

        expected = {
            "all": {"updates": {"funds[0].money_raised": {"old_value": 1000000, "new_value": None}}},
            "inserts": [],
            "updates": ["funds*"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)
        # now deletes the value
        del modified_json["funds"][0]["money_raised"]

        expected = {
            "all": {"deletes": {"funds[0].money_raised": {"old_value": 1000000}}},
            "inserts": [],
            "updates": [],
            "deletes": ["funds*"],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_insert_on_second_level_list(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["investments"][0]["funding_round"]["is_series"] = True

        expected = {
            "all": {"inserts": {"investments[0].funding_round.is_series": {"new_value": True}}},
            "inserts": ["investments*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_update_on_second_level_list(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["investments"][0]["funding_round"]["announced_on"] = "2019-10-11"

        expected = {
            "all": {
                "updates": {
                    "investments[0].funding_round.announced_on": {"old_value": "2019-10-10", "new_value": "2019-10-11"}
                }
            },
            "inserts": [],
            "updates": ["investments*"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_delete_on_second_level_list(self):
        modified_json = copy.deepcopy(self.original_json)
        del modified_json["investments"][0]["funding_round"]["announced_on"]

        expected = {
            "all": {"deletes": {"investments[0].funding_round.announced_on": {"old_value": "2019-10-10"}}},
            "inserts": [],
            "updates": [],
            "deletes": ["investments*"],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_insert_on_second_level_object(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["ipo"]["random_object"]["some"] = "thing"

        expected = {
            "all": {"inserts": {"ipo.random_object.some": {"new_value": "thing"}}},
            "inserts": ["ipo*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_update_on_second_level_object(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["ipo"]["random_object"]["ab"] = "dc"

        expected = {
            "all": {"updates": {"ipo.random_object.ab": {"old_value": "bc", "new_value": "dc"}}},
            "inserts": [],
            "updates": ["ipo*"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_delete_on_second_level_object(self):
        modified_json = copy.deepcopy(self.original_json)
        del modified_json["ipo"]["random_object"]["ab"]

        expected = {
            "all": {"deletes": {"ipo.random_object.ab": {"old_value": "bc"}}},
            "inserts": [],
            "updates": [],
            "deletes": ["ipo*"],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_insert_on_second_level_object_list_object(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["ipo"]["random_list"].append({"cd": "dc"})

        expected = {
            "all": {"inserts": {"ipo.random_list[1]": {"new_value": {"cd": "dc"}}}},
            "inserts": ["ipo*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_insert_on_second_level_object_list_value(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["ipo"]["random_list"][0]["cd"] = "dc"

        expected = {
            "all": {"inserts": {"ipo.random_list[0].cd": {"new_value": "dc"}}},
            "inserts": ["ipo*"],
            "updates": [],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_update_on_second_level_object_list(self):
        modified_json = copy.deepcopy(self.original_json)
        modified_json["ipo"]["random_list"][0]["ab"] = "abcd"

        expected = {
            "all": {"updates": {"ipo.random_list[0].ab": {"new_value": "abcd", "old_value": "bc"}}},
            "inserts": [],
            "updates": ["ipo*"],
            "deletes": [],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def test_delete_on_second_level_object_list(self):
        modified_json = copy.deepcopy(self.original_json)
        del modified_json["ipo"]["random_list"][0]["ab"]

        expected = {
            "all": {"deletes": {"ipo.random_list[0].ab": {"old_value": "bc"}}},
            "inserts": [],
            "updates": [],
            "deletes": ["ipo*"],
        }

        self._compare_diff(self.original_json, modified_json, expected)

    def _get_modifications_dict(self, modification_dict, _type):
        if _type not in modification_dict["all"]:
            modification_dict["all"][_type] = {}
        return modification_dict["all"][_type]

    def _get_inserts(self, translated_result):
        return self._get_modifications_dict(translated_result, "inserts")

    def _get_updates(self, translated_result):
        return self._get_modifications_dict(translated_result, "updates")

    def _get_deletes(self, translated_result):
        return self._get_modifications_dict(translated_result, "deletes")

    def _add_field_to_list(self, field_name, list_to_add):
        if "." in field_name:
            field_name = field_name.split(".")[0] + "*"

        if "[" in field_name:
            field_name = field_name.split("[")[0] + "*"

        list_to_add.add(field_name)

    def test_random_modifications(self):
        modified_json = copy.deepcopy(self.original_json)
        operations = ["insert", "update", "delete"]
        expected = {"all": {}, "inserts": [], "updates": [], "deletes": []}

        updates = set()
        deletes = set()
        inserts = set()

        for _ in range(1000):
            operation = random.choice(operations)

            keys = list(modified_json)
            key_to_modify = random.choice(keys)
            value_to_modify = modified_json[key_to_modify]

            if operation == "insert":
                new_key = "".join(random.choice(string.ascii_lowercase) for i in range(10))
                new_value = "".join(random.choice(string.ascii_lowercase) for i in range(10))
                modified_json[new_key] = new_value

                self._get_inserts(expected)[new_key] = {"new_value": new_value}
                self._add_field_to_list(new_key, inserts)
                expected["inserts"] = list(inserts)

            elif operation == "update":
                if isinstance(value_to_modify, dict):
                    keys_inside = list(value_to_modify)
                    key_inside_to_modify = random.choice(keys_inside)
                    value_inside_to_modify = value_to_modify[key_inside_to_modify]

                    original_value = self.original_json[key_to_modify][key_inside_to_modify]

                    new_value = None
                    if isinstance(value_inside_to_modify, str):
                        new_value = "".join(random.choice(string.ascii_lowercase) for i in range(10))
                    elif isinstance(value_inside_to_modify, (int, float)):
                        new_value = random.randint(0, 100000000)

                    if new_value is not None:
                        value_to_modify[key_inside_to_modify] = new_value

                        key_modified = "%s.%s" % (key_to_modify, key_inside_to_modify)
                        self._get_updates(expected)[key_modified] = {
                            "new_value": new_value,
                            "old_value": original_value,
                        }
                        self._add_field_to_list(key_modified, updates)
                        expected["updates"] = list(updates)
                else:
                    try:
                        original_value = self.original_json[key_to_modify]
                    except KeyError:
                        # this is a new key
                        continue

                    new_value = None
                    if isinstance(value_to_modify, str):
                        new_value = "".join(random.choice(string.ascii_lowercase) for i in range(10))
                    elif isinstance(value_to_modify, (int, float)):
                        new_value = random.randint(0, 100000000)

                    if new_value is not None:
                        modified_json[key_to_modify] = new_value
                        self._get_updates(expected)[key_to_modify] = {
                            "new_value": new_value,
                            "old_value": original_value,
                        }
                        self._add_field_to_list(key_to_modify, updates)
                        expected["updates"] = list(updates)

            else:
                if key_to_modify in updates or isinstance(value_to_modify, dict):
                    continue
                try:
                    original_value = self.original_json[key_to_modify]
                except KeyError:
                    # this is a new key
                    continue
                del modified_json[key_to_modify]

                self._get_deletes(expected)[key_to_modify] = {"old_value": original_value}
                self._add_field_to_list(key_to_modify, deletes)
                expected["deletes"] = list(deletes)

            self._compare_diff(self.original_json, modified_json, expected)
