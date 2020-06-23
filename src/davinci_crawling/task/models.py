# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import json
import logging
from datetime import datetime, date

from django.utils import timezone
import uuid

from caravaggio_rest_api.dse.columns import KeyEncodedMap
from caravaggio_rest_api.dse.models import CustomDjangoCassandraModel
from django.db.models.signals import pre_save
from django.dispatch import receiver

try:
    from dse.cqlengine import columns, ValidationError
    from dse.cqlengine.columns import UserDefinedType
    from dse.cqlengine.usertype import UserType
    from dse import ConsistencyLevel
except ImportError:
    from cassandra.cqlengine import columns, ValidationError
    from cassandra.cqlengine.columns import UserDefinedType
    from cassandra.cqlengine.usertype import UserType
    from cassandra import ConsistencyLevel

_logger = logging.getLogger("davinci_crawling.task")

STATUS_CREATED = 0
STATUS_QUEUED = 1
STATUS_IN_PROGRESS = 2
STATUS_FINISHED = 3
STATUS_FAULTY = 4
STATUS_UNKNOWN = 5
STATUS_MAINTENANCE = 6

ALL_STATUS = [
    STATUS_CREATED,
    STATUS_QUEUED,
    STATUS_IN_PROGRESS,
    STATUS_IN_PROGRESS,
    STATUS_FINISHED,
    STATUS_FAULTY,
    STATUS_UNKNOWN,
    STATUS_MAINTENANCE,
]

ON_DEMAND_TASK = 1
BATCH_TASK = 2

ALL_TASK_TYPES = [ON_DEMAND_TASK, BATCH_TASK]


class TaskMoreInfo(UserType):
    __type_name__ = "task_more_info"

    # from where the more info was created
    source = columns.Text()

    created_at = columns.DateTime()

    # details about the error
    details = columns.Text()


class Task(CustomDjangoCassandraModel):
    """
    Represents a task that could be an on demand task or a batch task.

    Args:
        task_id: the task id that is the unique partition key.
        user: The user that asked for the task, if it is an ondemand task.
        created_at: the date of the creation of the task.
        updated_at: the date that we last updated the task.
        is_deleted: controls if the data is deleted.
        status: representes the actual status of the task, could be:
            - 0 (Created)
            - 1 (Queued)
            - 2 (In Progress)
            - 3 (Finished)
            - 4 (Faulty)
            - 5 (Unknown)
        kind: the name of the crawler that will execute the task.
        params: the set of params used to execute the crawler command, this
        will be saved as Text.
        params_map: the exactly same content as `params` but saved on a way
        that we can search using solr (KeyEncodedMap).
        options: the set of options that is used to guide the crawler during
        the execution, this will be saved as text.
        options_map: the exactly same content as `options` but saved on a way
        that we can search using solr (KeyEncodedMap).
        times_performed: keep track on how many times the task was run.
        type: the type of the task, could be OnDemand(1) or Batch(2)
    """

    __table_name__ = "davinci_task"
    _cassandra_consistency_level_read = ConsistencyLevel.ONE
    _cassandra_consistency_level_write = ConsistencyLevel.ALL

    # Force that all the values will reside in the seam node of the cluster
    task_id = columns.UUID(partition_key=True, default=uuid.uuid4)

    # The owner of the data. Who own's the company data persisted
    user = columns.Text()

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=timezone.now, primary_key=True, clustering_order="DESC")
    updated_at = columns.DateTime(default=timezone.now)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)

    status = columns.SmallInt(default=STATUS_CREATED)

    kind = columns.Text(required=True)

    params_map = KeyEncodedMap(key_type=columns.Text, value_type=columns.Text)

    params = columns.Text(required=True)

    options_map = KeyEncodedMap(key_type=columns.Text, value_type=columns.Text)

    options = columns.Text(required=False)

    times_performed = columns.SmallInt(default=0)

    type = columns.SmallInt(default=ON_DEMAND_TASK)

    more_info = columns.List(value_type=UserDefinedType(TaskMoreInfo))

    differences_from_last_version = columns.Text()

    inserted_fields = columns.List(value_type=columns.Text)

    updated_fields = columns.List(value_type=columns.Text)

    deleted_fields = columns.List(value_type=columns.Text)

    changed_fields = columns.List(value_type=columns.Text)

    logging_task = columns.Boolean(default=False)

    class Meta:
        get_pk_field = "task_id"

    def validate(self):
        super().validate()

        if self.type not in ALL_TASK_TYPES:
            raise ValidationError("Invalid task type [{0}]. Valid types are: " "{1}.".format(self.type, ALL_TASK_TYPES))

        if self.status not in ALL_STATUS:
            raise ValidationError(
                "Invalid task status [{0}]. Valid status are: " "{1}.".format(self.status, ALL_STATUS)
            )


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=Task)
def pre_save_task(sender, instance=None, using=None, update_fields=None, **kwargs):
    params_string = generate_key_encoded_map(instance.params, instance.params_map)
    if params_string:
        instance.params = params_string

    instance.created_at = instance.created_at.replace(microsecond=0)

    options_string = generate_key_encoded_map(instance.options, instance.options_map)
    if options_string:
        instance.options = options_string

    if instance.logging_task:
        instance.updated_at = instance.created_at
    else:
        instance.updated_at = timezone.now()


def generate_key_encoded_map(json_map, key_encoded_map):
    """
    Gets a normal map and process it to be a KeyEncodedMap, as the
    KeyEncodedMap only accepts strings on the values we need to parse all the
    values to strings.
    Args:
        json_map: The original Map.
        key_encoded_map: The key enconded map that will be filled with the new
        data.

    Returns: A string representation of the json map.
    """
    if json_map and isinstance(json_map, dict):
        keys_to_remove = []
        for key, value in json_map.items():
            if value is None:
                keys_to_remove.append(key)
                continue
            if isinstance(value, datetime):
                string_date = value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                key_encoded_map[key] = string_date
                json_map[key] = string_date
            if isinstance(value, date):
                string_date = value.strftime("%Y-%m-%d")
                key_encoded_map[key] = string_date
                json_map[key] = string_date
            if isinstance(value, (list, dict)):
                key_encoded_map[key] = json.dumps(value)
            elif not isinstance(value, str):
                key_encoded_map[key] = str(value)
            else:
                key_encoded_map[key] = value

        for key in keys_to_remove:
            del json_map[key]

        return json.dumps(json_map)
