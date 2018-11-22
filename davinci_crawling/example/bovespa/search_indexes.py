# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

import logging
from django.utils import timezone

from haystack import indexes

from caravaggio_rest_api.indexes import BaseSearchIndex

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from .models import BovespaCompany, BovespaCompanyFile, BovespaAccount

_logger = logging.getLogger("{}.search_indexes".
                            format(BOVESPA_CRAWLER))


class BovespaCompanyIndex(BaseSearchIndex, indexes.Indexable):

    ccvm = indexes.CharField(model_attr="ccvm", faceted=True)

    # When was created the entity and the last modification date
    created_at = indexes.DateTimeField(
        model_attr="created_at", faceted=True)
    updated_at = indexes.DateTimeField(
        model_attr="updated_at", faceted=True)

    is_deleted = indexes.BooleanField(
        model_attr="is_deleted", faceted=True)
    deleted_reason = indexes.CharField(
        model_attr="deleted_reason")

    # The name of the company
    company_name = indexes.CharField(
        model_attr="company_name")

    # The company document (CNPJ)
    cnpj = indexes.CharField(
        model_attr="cnpj")

    # The company document (CNPJ)
    company_type = indexes.CharField(
        model_attr="company_type", faceted=True)

    situation = indexes.CharField(
        model_attr="situation", faceted=True)

    situation_date = indexes.DateField(
        model_attr="situation_date")

    class Meta:

        text_fields = ["deleted_reason", "company_name"]

        # Once the index has been created it cannot be changed
        # with sync_indexes. Changes should be made by hand.
        index_settings = {
            "realtime": "true",
            "autoCommitTime": "100",
            "ramBufferSize": "2048"
        }

    def get_model(self):
        return BovespaCompany

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            created_at__lte=timezone.now(),
            is_deleted=False
        )


class BovespaCompanyFileIndex(BaseSearchIndex, indexes.Indexable):

    ccvm = indexes.CharField(
        model_attr="ccvm", faceted=True)

    # The type of document
    doc_type = indexes.CharField(
        model_attr="doc_type", faceted=True)

    # The date of the data for the company
    fiscal_date = indexes.DateField(
        model_attr="fiscal_date", faceted=True)

    version = indexes.CharField(
        model_attr="version", faceted=True)

    status = indexes.CharField(
        model_attr="status", faceted=True)

    # When was created the entity and the last modification date
    created_at = indexes.DateTimeField(
        model_attr="created_at", faceted=True)
    updated_at = indexes.DateTimeField(
        model_attr="updated_at", faceted=True)

    is_deleted = indexes.BooleanField(
        model_attr="is_deleted", faceted=True)
    deleted_reason = indexes.CharField(
        model_attr="deleted_reason")

    # The url to the file that contains the information
    protocol = indexes.CharField(
        model_attr="protocol")

    # Date when the files where presented
    delivery_date = indexes.DateTimeField(
        model_attr="delivery_date", faceted=True)

    # The motivation of the delivery.
    delivery_type = indexes.CharField(
        model_attr="delivery_type", faceted=True)

    # The name of the company
    company_name = indexes.CharField(
        model_attr="company_name", faceted=True)

    # The cnpj of the company
    company_cnpj = indexes.CharField(
        model_attr="company_cnpj", faceted=True)

    # The Fiscal Date decomposed into year, quarter, month
    fiscal_date_y = indexes.IntegerField(
        model_attr="fiscal_date_y", faceted=True)
    fiscal_date_yd = indexes.IntegerField(
        model_attr="fiscal_date_yd", faceted=True)
    fiscal_date_q = indexes.IntegerField(
        model_attr="fiscal_date_q", faceted=True)
    fiscal_date_m = indexes.IntegerField(
        model_attr="fiscal_date_m", faceted=True)
    fiscal_date_md = indexes.IntegerField(
        model_attr="fiscal_date_md", faceted=True)
    fiscal_date_w = indexes.IntegerField(
        model_attr="fiscal_date_w", faceted=True)
    fiscal_date_wd = indexes.IntegerField(
        model_attr="fiscal_date_wd", faceted=True)
    fiscal_date_yq = indexes.CharField(
        model_attr="fiscal_date_yq", faceted=True)
    fiscal_date_ym = indexes.CharField(
        model_attr="fiscal_date_ym", faceted=True)

    # The url to the file that contains the information
    source_url = indexes.CharField(
        model_attr="source_url")

    # The url to the file that contains the information
    file_url = indexes.CharField(
        model_attr="file_url")

    # The name of the file
    file_name = indexes.CharField(
        model_attr="file_name")

    # The extension of the filename
    file_extension = indexes.CharField(
        model_attr="file_extension", faceted=True)

    # content = indexes.MultiValueField(
    #    null=True, model_attr="content", faceted=True)

    class Meta:

        text_fields = ["file_name", "source_url",
                       "company_name", "company_cnpj",
                       "delivery_type", "file_url", "deleted_reason"]

        # Once the index has been created it cannot be changed
        # with sync_indexes. Changes should be made by hand.
        index_settings = {
            "realtime": "true",
            "autoCommitTime": "100",
            "ramBufferSize": "2048"
        }

    def get_model(self):
        return BovespaCompanyFile

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            created_at__lte=timezone.now(),
            is_deleted=False
        )


class BovespaAccountIndex(BaseSearchIndex, indexes.Indexable):

    ccvm = indexes.CharField(
        model_attr="ccvm", faceted=True)

    # The date of the data for the company
    period = indexes.DateField(
        model_attr="period", faceted=True)

    number = indexes.CharField(
        model_attr="number", faceted=True)

    financial_info_type = indexes.CharField(
        model_attr="financial_info_type", faceted=True)

    balance_type = indexes.CharField(
        model_attr="balance_type", faceted=True)

    name = indexes.CharField(
        model_attr="name", faceted=True)

    value = indexes.DecimalField(
        model_attr="value")

    comments = indexes.CharField(
        model_attr="comments", faceted=True)

    # When was created the entity and the last modification date
    created_at = indexes.DateTimeField(
        model_attr="created_at", faceted=True)
    updated_at = indexes.DateTimeField(
        model_attr="updated_at", faceted=True)

    is_deleted = indexes.BooleanField(
        model_attr="is_deleted", faceted=True)
    deleted_reason = indexes.CharField(
        model_attr="deleted_reason")

    class Meta:

        text_fields = ["name", "comments", "deleted_reason"]

        # Once the index has been created it cannot be changed
        # with sync_indexes. Changes should be made by hand.
        index_settings = {
            "realtime": "true",
            "autoCommitTime": "100",
            "ramBufferSize": "2048"
        }

    def get_model(self):
        return BovespaAccount

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            created_at__lte=timezone.now(),
            is_deleted=False
        )
