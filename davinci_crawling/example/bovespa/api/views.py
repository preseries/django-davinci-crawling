# -*- coding: utf-8 -*
from drf_haystack.filters import HaystackFilter, HaystackBoostFilter, \
    HaystackGEOSpatialFilter, HaystackFacetFilter

from caravaggio_rest_api.drf_haystack.filters import \
    HaystackOrderingFilter

from caravaggio_rest_api.drf_haystack.viewsets import \
    CustomModelViewSet, CustomHaystackViewSet

# from rest_framework.authentication import \
#    TokenAuthentication, SessionAuthentication
# from rest_framework.permissions import IsAuthenticated

from drf_haystack import mixins

from .serializers import BovespaCompanySerializerV1, \
    BovespaCompanySearchSerializerV1, BovespaCompanyFacetSerializerV1, \
    BovespaCompanyFileSerializerV1, BovespaCompanyFileSearchSerializerV1, \
    BovespaCompanyFileFacetSerializerV1, \
    BovespaAccountSerializerV1, BovespaAccountSearchSerializerV1, \
    BovespaAccountFacetSerializerV1

from davinci_crawling.example.bovespa.models import \
    BovespaCompany, BovespaCompanyFile, BovespaAccount


class BovespaCompanyViewSet(CustomModelViewSet):
    queryset = BovespaCompany.objects.all()

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = BovespaCompanySerializerV1

    filter_fields = ("ccvm", "created_at", "updated_at", "situation")


class BovespaCompanySearchViewSet(mixins.FacetMixin, CustomHaystackViewSet):

    filter_backends = [
        HaystackFilter, HaystackBoostFilter,
        HaystackFacetFilter, HaystackOrderingFilter]

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [BovespaCompany]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = BovespaCompanySearchSerializerV1

    facet_serializer_class = BovespaCompanyFacetSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = BovespaCompanySerializerV1

    ordering_fields = (
        "ccvm", "cnpj", "company_name", "situation", "company_type",
        "granted_date", "canceled_date",
        "created_at", "updated_at")


class BovespaCompanyFileViewSet(CustomModelViewSet):
    queryset = BovespaCompanyFile.objects.all()

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = BovespaCompanyFileSerializerV1

    filter_fields = (
        "ccvm", "doc_type", "fiscal_date", "version",
        "created_at", "updated_at")


class BovespaCompanyFileSearchViewSet(
        mixins.FacetMixin, CustomHaystackViewSet):

    filter_backends = [
        HaystackFilter, HaystackBoostFilter,
        HaystackFacetFilter, HaystackOrderingFilter]

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [BovespaCompanyFile]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = BovespaCompanyFileSearchSerializerV1

    facet_serializer_class = BovespaCompanyFileFacetSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = BovespaCompanyFileSerializerV1

    ordering_fields = (
        "ccvm", "doc_type", "fiscal_date", "version", "status",
        "protocol", "delivery_date", "delivery_type",
        "company_name", "company_cnpj",
        "fiscal_date_y", "fiscal_date_yd", "fiscal_date_q",
        "fiscal_date_m", "fiscal_date_md", "fiscal_date_w",
        "fiscal_date_wd", "fiscal_date_yq", "fiscal_date_ym",
        "source_url", "file_url", "file_name", "file_extension"
        "created_at", "updated_at")


class BovespaAccountViewSet(CustomModelViewSet):
    queryset = BovespaAccount.objects.all()

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = BovespaAccountSerializerV1

    filter_fields = (
        "ccvm", "period", "number", "financial_info_type",
        "created_at", "updated_at")


class BovespaAccountSearchViewSet(mixins.FacetMixin, CustomHaystackViewSet):

    filter_backends = [
        HaystackFilter, HaystackBoostFilter,
        HaystackFacetFilter, HaystackOrderingFilter]

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [BovespaAccount]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = BovespaAccountSearchSerializerV1

    facet_serializer_class = BovespaAccountFacetSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = BovespaAccountSerializerV1

    ordering_fields = (
        "ccvm", "period", "number", "name",
        "financial_info_type", "balance_type", "comments",
        "value",
        "created_at", "updated_at",)
