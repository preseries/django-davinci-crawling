# -*- coding: utf-8 -*
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date

from caravaggio_rest_api.drf_haystack.serializers import \
    BaseCachedSerializerMixin, CustomHaystackSerializer
from drf_haystack.serializers import HaystackFacetSerializer

from rest_framework import fields, serializers

from rest_framework_cache.registry import cache_registry

from caravaggio_rest_api.drf_haystack import serializers as dse_serializers

from davinci_crawling.example.bovespa.models import \
    BovespaCompany, BovespaCompanyFile, BovespaAccount
from davinci_crawling.example.bovespa.search_indexes import \
    BovespaCompanyIndex, BovespaCompanyFileIndex, BovespaAccountIndex


class BovespaCompanySerializerV1(dse_serializers.CassandraModelSerializer,
                          BaseCachedSerializerMixin):
    """
    Represents a Business Object API View with support for JSON, list, and map
    fields.
    """

    class Meta:
        model = BovespaCompany
        fields = ("ccvm",
                  "created_at", "cnpj", "updated_at",
                  "company_name", "situation", "company_type",
                  "granted_date", "canceled_date")
        read_only_fields = ("created_at", "updated_at")


class BovespaCompanySearchSerializerV1(CustomHaystackSerializer,
                                BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    """

    score = fields.FloatField(required=False)

    class Meta(CustomHaystackSerializer.Meta):
        model = BovespaCompany
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [BovespaCompanyIndex]

        # The `fields` contains all the fields we want to include.
        # NOTE: Make sure you don't confuse these with model attributes. These
        # fields belong to the search index!
        fields = [
            "entity_type", "ccvm",
            "created_at", "cnpj", "updated_at",
            "company_name", "situation", "company_type",
            "granted_date", "canceled_date"
            "score"]


class BovespaCompanyFacetSerializerV1(HaystackFacetSerializer):

    # Setting this to True will serialize the
    # queryset into an `objects` list. This
    # is useful if you need to display the faceted
    # results. Defaults to False.
    serialize_objects = True

    class Meta:
        index_classes = [BovespaCompany]
        fields = ["created_at", "updated_at",
                  "situation", "company_type",
                  "granted_date", "canceled_date"]

        field_options = {
            "company_type": {},
            "situation": {},
            "created_at": {
                "start_date": datetime.now() - timedelta(days=5* 365),
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
            "granted_date": {
                "start_date": parse_date("1980-01-01"),
                "end_date": datetime.now(),
                "gap_by": "year",
                "gap_amount": 1
            },
            "canceled_date": {
                "start_date": parse_date("1980-01-01"),
                "end_date": datetime.now(),
                "gap_by": "year",
                "gap_amount": 1
            }
        }


# Cache configuration
cache_registry.register(BovespaCompanySerializerV1)
cache_registry.register(BovespaCompanySearchSerializerV1)


class BovespaCompanyFileSerializerV1(dse_serializers.CassandraModelSerializer,
                          BaseCachedSerializerMixin):
    """
    Represents a Business Object API View with support for JSON, list, and map
    fields.
    """

    class Meta:
        model = BovespaCompanyFile
        fields = ("ccvm", "doc_type", "fiscal_date", "version", "status",
                  "created_at", "updated_at",
                  "protocol", "delivery_date", "delivery_type",
                  "company_name", "company_cnpj",
                  "fiscal_date_y", "fiscal_date_yd", "fiscal_date_q",
                  "fiscal_date_m", "fiscal_date_md", "fiscal_date_w",
                  "fiscal_date_wd", "fiscal_date_yq", "fiscal_date_ym",
                  "source_url", "file_url", "file_name", "file_extension")
        read_only_fields = ("created_at", "updated_at")


class BovespaCompanyFileSearchSerializerV1(CustomHaystackSerializer,
                                BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    """

    score = fields.FloatField(required=False)

    class Meta(CustomHaystackSerializer.Meta):
        model = BovespaCompanyFile
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [BovespaCompanyFileIndex]

        # The `fields` contains all the fields we want to include.
        # NOTE: Make sure you don't confuse these with model attributes. These
        # fields belong to the search index!
        fields = [
            "ccvm", "doc_type", "fiscal_date", "version", "status",
            "created_at", "updated_at",
            "protocol", "delivery_date", "delivery_type",
            "company_name", "company_cnpj",
            "fiscal_date_y", "fiscal_date_yd", "fiscal_date_q",
            "fiscal_date_m", "fiscal_date_md", "fiscal_date_w",
            "fiscal_date_wd", "fiscal_date_yq", "fiscal_date_ym",
            "source_url", "file_url", "file_name", "file_extension"
            "score"]


class BovespaCompanyFileFacetSerializerV1(HaystackFacetSerializer):

    # Setting this to True will serialize the
    # queryset into an `objects` list. This
    # is useful if you need to display the faceted
    # results. Defaults to False.
    serialize_objects = True

    class Meta:
        index_classes = [BovespaCompany]
        fields = [
            "ccvm", "doc_type", "fiscal_date", "version", "status",
            "created_at", "updated_at",
            "delivery_date", "delivery_type",
            "company_name", "company_cnpj",
            "fiscal_date_y", "fiscal_date_yd", "fiscal_date_q",
            "fiscal_date_m", "fiscal_date_md", "fiscal_date_w",
            "fiscal_date_wd", "fiscal_date_yq", "fiscal_date_ym",
            "file_extension"]

        field_options = {
            "ccvm": {},
            "doc_type": {},
            "version": {},
            "status": {},
            "company_name": {},
            "company_cnpj": {},
            "fiscal_date_y": {},
            "fiscal_date_yd": {},
            "fiscal_date_q": {},
            "fiscal_date_m": {},
            "fiscal_date_md": {},
            "fiscal_date_w": {},
            "fiscal_date_wd": {},
            "fiscal_date_yq": {},
            "fiscal_date_ym": {},
            "file_extension": {},
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
            "delivery_date": {
                "start_date": parse_date("2000-01-01"),
                "end_date": datetime.now(),
                "gap_by": "year",
                "gap_amount": 1
            },
            "fiscal_date": {
                "start_date": parse_date("2000-01-01"),
                "end_date": datetime.now(),
                "gap_by": "year",
                "gap_amount": 1
            }
        }


# Cache configuration
cache_registry.register(BovespaCompanyFileSerializerV1)
cache_registry.register(BovespaCompanyFileSearchSerializerV1)


class BovespaAccountSerializerV1(dse_serializers.CassandraModelSerializer,
                          BaseCachedSerializerMixin):
    """
    Represents a Business Object API View with support for JSON, list, and map
    fields.
    """

    class Meta:
        model = BovespaAccount
        fields = ("ccvm", "period", "number", "financial_info_type",
                  "balance_type", "name", "value",
                  "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")



class BovespaAccountSearchSerializerV1(CustomHaystackSerializer,
                                BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    """

    score = fields.FloatField(required=False)

    class Meta(CustomHaystackSerializer.Meta):
        model = BovespaAccount
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [BovespaAccountIndex]

        # The `fields` contains all the fields we want to include.
        # NOTE: Make sure you don't confuse these with model attributes. These
        # fields belong to the search index!
        fields = [
            "ccvm", "period", "number", "name",
            "financial_info_type", "balance_type", "comments",
            "value",
            "created_at", "updated_at",
            "score"]


class BovespaAccountFacetSerializerV1(HaystackFacetSerializer):

    # Setting this to True will serialize the
    # queryset into an `objects` list. This
    # is useful if you need to display the faceted
    # results. Defaults to False.
    serialize_objects = True

    class Meta:
        index_classes = [BovespaAccount]
        fields = [
            "ccvm", "period", "number", "name",
            "financial_info_type", "balance_type", "comments",
            "created_at", "updated_at"]

        field_options = {
            "ccvm": {},
            "number": {},
            "name": {},
            "financial_info_type": {},
            "balance_type": {},
            "comments": {},
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
            "period": {
                "start_date": parse_date("2000-01-01"),
                "end_date": datetime.now(),
                "gap_by": "year",
                "gap_amount": 1
            },
        }


# Cache configuration
cache_registry.register(BovespaAccountSerializerV1)
cache_registry.register(BovespaAccountSearchSerializerV1)