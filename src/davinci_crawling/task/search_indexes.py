# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging
from datetime import datetime

from haystack import indexes

from caravaggio_rest_api.haystack.indexes import BaseSearchIndex, TextField

from .models import Task

_logger = logging.getLogger("davinci_crawler.tasl.search_indexes")


class TaskIndex(BaseSearchIndex, indexes.Indexable):

    task_id = indexes.CharField(model_attr="task_id")

    user = indexes.CharField(model_attr="user")

    created_at = indexes.DateTimeField(model_attr="created_at", faceted=True)

    updated_at = indexes.DateTimeField(model_attr="updated_at")

    is_deleted = indexes.BooleanField(model_attr="is_deleted", faceted=True)

    status = indexes.IntegerField(model_attr="status", faceted=True)

    kind = indexes.CharField(model_attr="kind", faceted=True)

    params_map = indexes.MultiValueField(null=True, model_attr="params_map")

    options_map = indexes.MultiValueField(null=True, model_attr="options_map")

    times_performed = indexes.IntegerField(model_attr="times_performed")

    type = indexes.IntegerField(model_attr="type", faceted=True)

    more_info = indexes.MultiValueField(model_attr="more_info")

    differences_from_last_version = TextField(model_attr="differences_from_last_version")

    inserted_fields = indexes.MultiValueField(model_attr="inserted_fields")

    updated_fields = indexes.MultiValueField(model_attr="updated_fields")

    deleted_fields = indexes.MultiValueField(model_attr="deleted_fields")

    changed_fields = indexes.MultiValueField(model_attr="changed_fields")

    logging_task = indexes.BooleanField(model_attr="logging_task")

    class Meta:

        text_fields = []

        exclude = ["params", "options"]

        # Once the index has been created it cannot be changed
        # with sync_indexes. Changes should be made by hand.
        index_settings = {"realtime": "true", "autoCommitTime": "100", "ramBufferSize": "2048"}

    def get_model(self):
        return Task

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(created_at__lte=datetime.utcnow(), is_deleted=False)
