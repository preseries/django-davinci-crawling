# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
from caravaggio_rest_api.drf_haystack.viewsets import \
    CaravaggioCassandraModelViewSet, \
    CaravaggioHaystackGEOSearchViewSet, \
    CaravaggioHaystackFacetSearchViewSet

# from rest_framework.authentication import \
#    TokenAuthentication, SessionAuthentication
# from rest_framework.permissions import IsAuthenticated

from drf_haystack import mixins

from .serializers import Bgds_taskResourceSerializerV1, \
    Bgds_taskResourceSearchSerializerV1, \
    Bgds_taskResourceGEOSearchSerializerV1, \
    Bgds_taskResourceFacetSerializerV1

from bgds_task.models import Bgds_taskResource


class Bgds_taskResourceViewSet(CaravaggioCassandraModelViewSet):
    queryset = Bgds_taskResource.objects.all()

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = Bgds_taskResourceSerializerV1


class Bgds_taskResourceSearchViewSet(CaravaggioHaystackFacetSearchViewSet):

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [Bgds_taskResource]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = Bgds_taskResourceSearchSerializerV1

    facet_serializer_class = Bgds_taskResourceFacetSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = Bgds_taskResourceSerializerV1

    ordering_fields = (
        "_id", "name", "short_description", "long_description",
        "situation", "crawl_param",
        "created_at", "updated_at")


class Bgds_taskResourceGEOSearchViewSet(CaravaggioHaystackGEOSearchViewSet):

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [Bgds_taskResource]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = Bgds_taskResourceGEOSearchSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = Bgds_taskResourceSerializerV1

    ordering_fields = ("_id", "created_at", "updated_at", "foundation_date",
                       "country_code", "specialties")
