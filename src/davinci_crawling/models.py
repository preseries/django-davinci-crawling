# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import json
from datetime import datetime

from django.db.models.signals import pre_save
from django.dispatch import receiver

try:
    from dse.cqlengine import columns, ValidationError
except ImportError:
    from cassandra.cqlengine import columns, ValidationError

from caravaggio_rest_api.dse.models import CustomDjangoCassandraModel
from caravaggio_rest_api.utils import default


class Checkpoint(CustomDjangoCassandraModel):

    __table_name__ = "davinci_checkpoint"

    source = columns.Text(partition_key=True)

    key = columns.Text(primary_key=True)

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)
    deleted_reason = columns.Text()

    data = columns.Text(required=False)

    class Meta:
        get_pk_field = "source"

    def get_data(self):
        return json.loads(self.data)

    def set_data(self, json_data):
        self.data = json.dumps(json_data, sort_keys=True, indent=4, default=default)


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=Checkpoint)
def set_update_at(sender, instance=None, **kwargs):
    instance.updated_at = datetime.utcnow()
