# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.

from caravaggio_rest_api.drf_haystack.serializers import \
    BaseCachedSerializerMixin, CustomHaystackSerializer
from drf_haystack.serializers import HaystackFacetSerializer

from rest_framework import fields, serializers

from rest_framework_cache.registry import cache_registry

from caravaggio_rest_api.drf_haystack import serializers as dse_serializers
from caravaggio_rest_api import fields as dse_fields

from davinci_crawling.task.models import Task, ON_DEMAND_TASK, STATUS_CREATED
from davinci_crawling.task.search_indexes import TaskIndex


class TaskSerializerV1(
        dse_serializers.CassandraModelSerializer, BaseCachedSerializerMixin):
    """
    Represents a Business Object API View with support for JSON and map
    fields.
    """
    user = serializers.HiddenField(
        default=dse_fields.CurrentUserNameDefault())

    params = fields.JSONField(required=True)

    options = fields.JSONField(required=True)

    type = serializers.IntegerField(default=ON_DEMAND_TASK)
    status = serializers.IntegerField(default=STATUS_CREATED)

    params_map = fields.DictField(child=fields.CharField(), required=False)
    options_map = fields.DictField(child=fields.CharField(), required=False)
    kind = fields.CharField(required=True)

    class Meta:
        model = Task
        fields = ("task_id", "user",
                  "created_at", "updated_at",
                  "is_deleted", "status", "kind",
                  "params", "times_performed",
                  "type", "params_map", "options", "options_map")
        read_only_fields = ("user", "created_at", "updated_at",
                            "is_deleted", "status",
                            "times_performed", "type", "params_map",
                            "options_map")


class TaskSearchSerializerV1(
        CustomHaystackSerializer, BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    """
    user = serializers.HiddenField(
        default=dse_fields.CurrentUserNameDefault())
    type = serializers.IntegerField(default=ON_DEMAND_TASK)
    status = serializers.IntegerField(default=STATUS_CREATED)

    params = fields.DictField(required=True, child=fields.CharField())
    kind = fields.CharField(required=True)

    class Meta(CustomHaystackSerializer.Meta):
        model = Task
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [TaskIndex]

        # The `fields` contains all the fields we want to include.
        # NOTE: Make sure you don't confuse these with model attributes. These
        # fields belong to the search index!
        fields = [
            "task_id", "user",
            "created_at", "updated_at",
            "is_deleted", "status", "kind",
            "params", "times_performed",
            "type"
        ]


class TaskFacetSerializerV1(HaystackFacetSerializer):
    """
    A facet view to use facets on the API.
    """
    # Setting this to True will serialize the
    # queryset into an `objects` list. This
    # is useful if you need to display the faceted
    # results. Defaults to False.
    serialize_objects = True

    class Meta:
        index_classes = [Task]
        fields = ["task_id", "user",
                  "created_at", "updated_at",
                  "is_deleted", "status", "kind",
                  "params", "times_performed",
                  "type"]

        field_options = {
            "type": {},
            "status": {},
            "kind": {},
        }


# Cache configuration
cache_registry.register(TaskSerializerV1)
cache_registry.register(TaskSearchSerializerV1)
