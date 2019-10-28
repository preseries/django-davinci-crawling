# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
from caravaggio_rest_api.drf_haystack.viewsets import \
    CaravaggioCassandraModelViewSet, \
    CaravaggioHaystackGEOSearchViewSet, \
    CaravaggioHaystackFacetSearchViewSet

from .serializers import TaskSerializerV1, \
    TaskSearchSerializerV1, \
    TaskFacetSerializerV1

from davinci_crawling.task.models import Task


class TaskViewSet(CaravaggioCassandraModelViewSet):
    queryset = Task.objects.all()

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = TaskSerializerV1
    http_method_names = ['get', 'post', 'delete']


class TaskSearchViewSet(CaravaggioHaystackFacetSearchViewSet):

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [Task]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = TaskSearchSerializerV1

    facet_serializer_class = TaskFacetSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = TaskSerializerV1

    ordering_fields = (
        "_id", "name", "short_description", "long_description",
        "situation", "crawl_param",
        "created_at", "updated_at")
