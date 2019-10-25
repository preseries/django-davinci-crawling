# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date

from caravaggio_rest_api.drf_haystack.serializers import \
    BaseCachedSerializerMixin, CustomHaystackSerializer
from drf_haystack.serializers import HaystackFacetSerializer

from rest_framework import fields, serializers

from rest_framework_cache.registry import cache_registry

from caravaggio_rest_api.drf_haystack import serializers as dse_serializers
from caravaggio_rest_api import fields as dse_fields

from bgds_task.models import Task
from bgds_task.search_indexes import TaskIndex


class TaskSerializerV1(
        dse_serializers.CassandraModelSerializer, BaseCachedSerializerMixin):
    """
    Represents a Business Object API View with support for JSON, list, and map
    fields.
    """
    user = serializers.HiddenField(
        default=dse_fields.CurrentUserNameDefault())

    specialties = fields.ListField(required=False, child=fields.CharField())

    websites = fields.DictField(required=False, child=fields.CharField())

    extra_data = dse_fields.CassandraJSONFieldAsText(required=False)

    class Meta:
        model = Task
        fields = ("_id", "user",
                  "created_at", "updated_at",
                  "name", "short_description", "long_description",
                  "situation", "crawl_param",
                  "foundation_date", "country_code",
                  "latitude", "longitude", "specialties", "websites",
                  "extra_data")
        read_only_fields = ("_id", "user", "created_at", "updated_at")


class Bgds_taskResourceSearchSerializerV1(
        CustomHaystackSerializer, BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    """
    user = serializers.HiddenField(
        default=dse_fields.CurrentUserNameDefault())

    specialties = fields.ListField(required=False, child=fields.CharField())

    websites = fields.DictField(required=False, child=fields.CharField())

    extra_data = dse_fields.CassandraJSONFieldAsText(required=False)

    score = fields.FloatField(required=False)

    class Meta(CustomHaystackSerializer.Meta):
        model = Bgds_taskResource
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [Bgds_taskResourceIndex]

        # The `fields` contains all the fields we want to include.
        # NOTE: Make sure you don't confuse these with model attributes. These
        # fields belong to the search index!
        fields = [
            "_id", "user",
            "created_at", "updated_at",
            "name", "short_description", "long_description",
            "situation", "crawl_param", "foundation_date", "country_code",
            "latitude", "longitude", "specialties", "websites",
            "extra_data",
            "text", "score"]


class Bgds_taskResourceGEOSearchSerializerV1(
        Bgds_taskResourceSearchSerializerV1):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    to do GEO Spatial searches
    """
    distance = dse_fields.DistanceField(required=False, units="m")

    class Meta(CustomHaystackSerializer.Meta):
        model = Bgds_taskResource
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [Bgds_taskResourceIndex]

        fields = [
            "_id", "user",
            "created_at", "updated_at",
            "name", "short_description", "long_description",
            "situation", "crawl_param", "foundation_date", "country_code",
            "latitude", "longitude", "specialties", "websites",
            "extra_data",
            "text", "score", "distance"
        ]


class Bgds_taskResourceFacetSerializerV1(HaystackFacetSerializer):

    # Setting this to True will serialize the
    # queryset into an `objects` list. This
    # is useful if you need to display the faceted
    # results. Defaults to False.
    serialize_objects = True

    class Meta:
        index_classes = [Bgds_taskResource]
        fields = ["created_at", "updated_at", "situation", 'crawl_param',
                  "specialties", "foundation_date", "country_code"]

        field_options = {
            "situation": {},
            "country_code": {},
            "specialties": {},
            "crawl_param": {},
            "foundation_date": {
                "start_date": datetime.now() - timedelta(days=50 * 365),
                "end_date": datetime.now(),
                "gap_by": "month",
                "gap_amount": 6
            },
            "created_at": {
                "start_date": datetime.now() - timedelta(days=5 * 365),
                "end_date": datetime.now(),
                "gap_by": "month",
                "gap_amount": 1
            },
            "updated_at": {
                "start_date": datetime.now() - timedelta(days=5 * 365),
                "end_date": datetime.now(),
                "gap_by": "month",
                "gap_amount": 1
            },
        }


# Cache configuration
cache_registry.register(Bgds_taskResourceSerializerV1)
cache_registry.register(Bgds_taskResourceSearchSerializerV1)
cache_registry.register(Bgds_taskResourceGEOSearchSerializerV1)
