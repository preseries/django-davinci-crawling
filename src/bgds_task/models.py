# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging
from django.utils import timezone
import uuid

from caravaggio_rest_api.dse.columns import \
    KeyEncodedMap
from caravaggio_rest_api.dse.models import \
    CustomDjangoCassandraModel
from django.db.models.signals import pre_save
from django.dispatch import receiver

try:
    from dse.cqlengine import columns, ValidationError
except ImportError:
    from cassandra.cqlengine import columns, ValidationError

from bgds_task import CRAWLER_NAME

_logger = logging.getLogger("davinci_crawler_{}.models".format(CRAWLER_NAME))

STATUS_CREATED = 0
STATUS_QUEUED = 1
STATUS_IN_PROGRESS = 2
STATUS_FINISHED = 3
STATUS_FAULTY = 4
STATUS_UNKNOWN = 5

ALL_STATUS = [STATUS_CREATED, STATUS_QUEUED, STATUS_IN_PROGRESS,
              STATUS_IN_PROGRESS, STATUS_FINISHED, STATUS_FAULTY,
              STATUS_UNKNOWN]

ON_DEMAND_TASK = 1
BATCH_TASK = 2

ALL_TASK_TYPES = [ON_DEMAND_TASK, BATCH_TASK]


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
        params: the set of params used to execute the crawler command.
        times_performed: keep track on how many times the task was run.
        type: the type of the task, could be OnDemand(1) or Batch(2)
    """

    __table_name__ = "task"

    # Force that all the values will reside in the seam node of the cluster
    task_id = columns.UUID(partition_key=True, default=uuid.uuid4)

    # The owner of the data. Who own's the company data persisted
    user = columns.Text()

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=timezone.now)
    updated_at = columns.DateTime(default=timezone.now)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)

    status = columns.SmallInt()

    kind = columns.Text()

    params = KeyEncodedMap(
        key_type=columns.Text, value_type=columns.Text)

    times_performed = columns.SmallInt(default=0)

    type = columns.SmallInt()

    class Meta:
        get_pk_field = "task_id"

    def validate(self):
        super().validate()

        if self.type not in ALL_TASK_TYPES:
            raise ValidationError(
                "Invalid task type [{0}]. Valid types are: "
                "{1}.".format(self.type, ALL_TASK_TYPES))

        if self.status not in ALL_STATUS:
            raise ValidationError(
                "Invalid task type [{0}]. Valid types are: "
                "{1}.".format(self.status, ALL_STATUS))


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=Task)
def pre_save_task(
        sender, instance=None, using=None, update_fields=None, **kwargs):
    instance.updated_at = timezone.now()
