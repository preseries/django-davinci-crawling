# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
from jsondiff import diff
from jsondiff.symbols import Symbol


def _get_translated_result(translated_result, _type):
    if _type not in translated_result:
        translated_result[_type] = {}
    return translated_result[_type]


def _get_inserts(translated_result):
    return _get_translated_result(translated_result, "inserts")


def _get_updates(translated_result):
    return _get_translated_result(translated_result, "updates")


def _get_deletes(translated_result):
    return _get_translated_result(translated_result, "deletes")


def _translate(json_diff_result, translated_result, inserted_fields,
               updated_fields, deleted_fields, last_field=""):
    """
    Translates the json diff format of response to our format of response.
    Args:
        json_diff_result: the pure json diff response;
        translated_result: the dict that will store the translated response;
        inserted_fields: the name of the fields that have been inserted;
        updated_fields: the name of the fields that have been updated;
        deleted_fields: the name of the fields that have been deleted;
        last_field: when we have a change on a multi-level dict we need to
            iterate over the levels and because of that we need to know the
            name of the last field

    Returns:

    """
    if last_field:
        last_field += "."

    for key, value in json_diff_result.items():
        if isinstance(key, Symbol):
            if str(key) == "$insert":
                if isinstance(value, dict):
                    for field, value_field in value.items():
                        _get_inserts(translated_result)[last_field + field] = {
                            "new_value": value_field
                        }
                        inserted_fields.append(last_field + field)
                elif isinstance(value, list):
                    for tuple_val in value:
                        # this guy is inserting a whole object on this position
                        if isinstance(tuple_val, tuple):
                            position = tuple_val[0]
                            last_field = "%s[%s]" % (last_field[0:-1],
                                                     position)

                            _get_inserts(translated_result)[last_field] = {
                                "new_value": tuple_val[1]
                            }
                            inserted_fields.append(last_field)
            elif str(key) == "$delete":
                if isinstance(value, dict):
                    for field, value_field in value.items():
                        _get_deletes(translated_result)[last_field + field] = {
                            "old_value": value_field
                        }
                        deleted_fields.append(last_field + field)
                elif isinstance(value, list):
                    for tuple_val in value:
                        # this guy is inserting a whole object on this position
                        if isinstance(tuple_val, tuple):
                            position = tuple_val[0]
                            last_field = "%s[%s]" % (last_field[0:-1],
                                                     position)

                            _get_deletes(translated_result)[last_field] = {
                                "old_value": tuple_val[1]
                            }
                            deleted_fields.append(last_field)

        elif isinstance(key, str):
            # this is when jsondiff founds an update on the value
            if isinstance(value, list):
                old_value = value[0]
                new_value = value[1]
                _get_updates(translated_result)[last_field + key] = {
                    "new_value": new_value,
                    "old_value": old_value
                }
                updated_fields.append(last_field + key)
            # this is when we have a change in a multilevel environment
            elif isinstance(value, dict):
                _translate(value, translated_result, inserted_fields,
                           updated_fields, deleted_fields,
                           last_field + key)

        # when the key is int it's because we're dealing with a one_to_many
        # dict
        elif isinstance(key, int):
            # remove the dot from the string and add [] to represent
            # position
            last_field = "%s[%s]" % (last_field[0:-1], key)
            _translate(value, translated_result, inserted_fields,
                       updated_fields, deleted_fields, last_field)


def make_diff(previous_json, current_json):
    result = diff(previous_json, current_json, syntax='symmetric')

    translated_result = {}
    inserted_fields = []
    updated_fields = []
    deleted_fields = []

    _translate(result, translated_result, inserted_fields, updated_fields,
               deleted_fields)

    final_result = {
        "all": translated_result,
        "inserts": inserted_fields,
        "updates": updated_fields,
        "deletes": deleted_fields
    }

    return final_result
