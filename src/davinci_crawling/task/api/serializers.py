# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.

from caravaggio_rest_api.drf_haystack.serializers import BaseCachedSerializerMixin, CustomHaystackSerializer
from drf_haystack.serializers import HaystackFacetSerializer

from rest_framework import fields, serializers

from rest_framework_cache.registry import cache_registry

from caravaggio_rest_api.drf_haystack import serializers as dse_serializers
from caravaggio_rest_api import fields as dse_fields

from davinci_crawling.task.models import Task, ON_DEMAND_TASK, STATUS_CREATED, TaskMoreInfo
from davinci_crawling.task.search_indexes import TaskIndex


class TaskMoreInfoSerializer(dse_serializers.UserTypeSerializer):
    source = serializers.CharField(required=False, allow_null=True)

    created_at = serializers.DateTimeField(required=False, allow_null=True)

    details = serializers.CharField(required=False, allow_null=True)

    class Meta(object):
        """Meta options."""

        __type__ = TaskMoreInfo


class TaskSerializerV1(dse_serializers.CassandraModelSerializer, BaseCachedSerializerMixin):
    """
    Represents a Business Object API View with support for JSON and map
    fields.
    """

    user = serializers.HiddenField(default=dse_fields.CurrentUserNameDefault())

    params = dse_fields.CassandraJSONFieldAsText(
        required=True, help_text="the set of params used to execute the crawler" " command, this will be saved as Text."
    )

    options = dse_fields.CassandraJSONFieldAsText(
        required=False,
        help_text="the exactly same content as `options` but saved"
        " on a way that we can search using solr "
        "(KeyEncodedMap).",
    )

    more_info = fields.ListField(required=False, allow_null=True, child=TaskMoreInfoSerializer())

    differences_from_last_version = fields.JSONField(required=False, allow_null=True)

    inserted_fields = fields.ListField(required=False, allow_null=True, child=serializers.CharField())

    updated_fields = fields.ListField(required=False, allow_null=True, child=serializers.CharField())

    deleted_fields = fields.ListField(required=False, allow_null=True, child=serializers.CharField())

    changed_fields = fields.ListField(required=False, allow_null=True, child=serializers.CharField())

    class Meta:
        model = Task
        fields = (
            "task_id",
            "user",
            "created_at",
            "updated_at",
            "is_deleted",
            "status",
            "kind",
            "params",
            "times_performed",
            "type",
            "options",
            "more_info",
            "differences_from_last_version",
            "inserted_fields",
            "updated_fields",
            "deleted_fields",
            "changed_fields",
            "logging_task",
        )
        read_only_fields = (
            "user",
            "created_at",
            "updated_at",
            "is_deleted",
            "status",
            "times_performed",
            "type",
            "params_map",
            "options_map",
            "differences_from_last_version",
            "inserted_fields",
            "updated_fields",
            "deleted_fields",
            "changed_fields",
            "logging_task",
        )
        extra_kwargs = {
            "task_id": {"help_text": "the task id that is the unique partition key."},
            "user": {"help_text": "The user that asked for the task, if it is an " "ondemand task."},
            "created_at": {"help_text": "the date of the creation of the task."},
            "updated_at": {"help_text": "the date that we last updated the task."},
            "is_deleted": {"help_text": "controls if the data is deleted."},
            "status": {
                "help_text": """
                 represents the actual status of the task, could be:
                    - 0 (Created)
                    - 1 (Queued)
                    - 2 (In Progress)
                    - 3 (Finished)
                    - 4 (Faulty)
                    - 5 (Unknown)
                """,
                "default": STATUS_CREATED,
            },
            "kind": {"help_text": "the name of the crawler that will execute the " "task."},
            "times_performed": {"help_text": "keep track on how many times the task was run."},
            "type": {
                "help_text": "the type of the task, could be OnDemand(1) or " "Batch(2)",
                "default": ON_DEMAND_TASK,
            },
            "more_info": {
                "help_text": "more info about the task, for example, something" "about the maintenance state"
            },
        }


class TaskSearchSerializerV1(CustomHaystackSerializer, BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    """

    user = serializers.HiddenField(default=dse_fields.CurrentUserNameDefault())
    type = serializers.IntegerField(default=ON_DEMAND_TASK)
    status = serializers.IntegerField(default=STATUS_CREATED)

    params = dse_fields.CassandraJSONFieldAsText(required=True)
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
            "task_id",
            "user",
            "created_at",
            "updated_at",
            "is_deleted",
            "status",
            "kind",
            "params_map",
            "options_map",
            "times_performed",
            "type",
            "logging_task",
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
        fields = [
            "created_at",
            "is_deleted",
            "status",
            "kind",
            "type",
        ]

        field_options = {}


# Cache configuration
cache_registry.register(TaskSerializerV1)
cache_registry.register(TaskSearchSerializerV1)
