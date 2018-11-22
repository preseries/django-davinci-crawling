# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

import logging
from datetime import datetime
from caravaggio_rest_api.dse_models import CustomDjangoCassandraModel
from django.db.models.signals import pre_save
from django.dispatch import receiver

try:
    from dse.cqlengine import columns, ValidationError
except ImportError:
    from cassandra.cqlengine import columns, ValidationError

from caravaggio_rest_api.utils import week_of_year, quarter

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER

SITUATION_CANCELLED = "CANCELED"
SITUATION_GRANTED = "GRANTED"

SITUATIONS = [SITUATION_CANCELLED, SITUATION_GRANTED]

DOC_TYPE_ITR = "ITR"
DOC_TYPE_DFP = "DFP"
DOC_TYPES = [DOC_TYPE_ITR, DOC_TYPE_DFP]

FILE_STATUS_NOT_PROCESSED = "not_processed"
FILE_STATUS_PROCESSED = "processed"
FILE_STATUSES = [FILE_STATUS_NOT_PROCESSED, FILE_STATUS_PROCESSED]

_logger = logging.getLogger("{}.models".
                            format(BOVESPA_CRAWLER))


class BovespaCompany(CustomDjangoCassandraModel):

    __table_name__ = "bovespa_company"

    # Force that all the values will reside in the seam node of the cluster
    entity_type = columns.Text(partition_key=True, default="company")

    # ID of the company in B3
    ccvm = columns.Text(primary_key=True)

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)
    deleted_reason = columns.Text()

    company_name = columns.Text(required=True)

    cnpj = columns.Text()

    company_type = columns.Text()

    situation = columns.Text(required=True)

    granted_date = columns.Date()
    canceled_date = columns.Date()

    class Meta:
        get_pk_field = "entity_type"

    def validate(self):
        super().validate()

        if self.situation not in SITUATIONS:
            raise ValidationError(
                "Invalid situation [{0}]. Valid situations are: {1}.".
                    format(self.situation, SITUATIONS))


class BovespaCompanyFile(CustomDjangoCassandraModel):

    __table_name__ = "bovespa_company_file"

    # ID of the company in B3
    ccvm = columns.Text(partition_key=True)

    # The type of document
    doc_type = columns.Text(max_length=3, primary_key=True)

    # The fiscal date the file is making reference.
    fiscal_date = columns.Date(primary_key=True, clustering_order="DESC")

    # The file version. The company could present different version of
    # the files for a specific fiscal period
    version = columns.Text(primary_key=True, clustering_order="DESC")

    status = columns.Text(default=FILE_STATUS_NOT_PROCESSED)

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)
    deleted_reason = columns.Text()

    # The protocol code associated with the file
    protocol = columns.Text(required=True)

    # When the documents were delivered
    delivery_date = columns.DateTime(required=True)

    # Why the files were delivered
    delivery_type = columns.Text(required=True)

    # The official name of the company
    company_name = columns.Text(required=True)

    # The company CNPJ
    company_cnpj = columns.Text(required=True)

    # The Fiscal Period decomposed into year, quarter, month
    # The year of the balance sheet
    # Ex. 2015
    fiscal_date_y = columns.SmallInt()

    # The day of the year of the balance sheet
    # Ex. 2015
    fiscal_date_yd = columns.SmallInt()

    # The quarter of the balance sheet
    # Ex. 1
    fiscal_date_q = columns.SmallInt()

    # The month of the balance sheet
    # Ex. 1
    fiscal_date_m = columns.SmallInt()

    # The day of the month of the balance sheet
    # Ex. 1
    fiscal_date_md = columns.SmallInt()

    # The week of the year
    # Ex. 1
    fiscal_date_w = columns.SmallInt()

    # The day of the week of the year
    # Ex. 1
    fiscal_date_wd = columns.SmallInt()

    # Combination of YEAR-QUARTER in the form of 2018-Q1
    # That allows us to facet results per quarter
    fiscal_date_yq = columns.Text()

    # Combination of YEAR-MONTH in the form of 2018-01
    # That allows us to facet results per month
    fiscal_date_ym = columns.Text()

    # The url to the file that contains the information in bovespa. This
    # will be the url we will use to download the file from the source
    source_url = columns.Text(required=True)

    # The url to the file that contains the information. Is an url to a
    # repository of our own. The file has already beed downloaded and
    # persisted into a custom repository. We do not need to access the source
    file_url = columns.Text()

    # The internal name of the file
    file_name = columns.Text()

    # The extension of the filename
    file_extension = columns.Text()

    # Each key represents the name of the file in the ENER arquive.
    # The value is the original content converted into JSON - when possible -
    # and persisted as Text
    # content = KeyEncodedMap(
    #    key_type=columns.Text, value_type=columns.Text)

    class Meta:
        get_pk_field = "ccvm"

    def validate(self):
        super().validate()

        if self.doc_type not in DOC_TYPES:
            raise ValidationError(
                "Invalid doc type [{0}]. Valid types are: {1}.".
                format(self.doc_type, DOC_TYPES))

        if self.status not in FILE_STATUSES:
            raise ValidationError(
                "Invalid file status [{0}]. Valid statuses are: {1}.".
                format(self.status, FILE_STATUSES))


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=BovespaCompanyFile)
def pre_save_bovespa_company_file(
        sender, instance=None, using=None, update_fields=None, **kwargs):
    instance.updated_at = datetime.utcnow()

    if instance.fiscal_date:
        date_data = instance.fiscal_date.date().timetuple()
        instance.fiscal_date_y = date_data.tm_year
        instance.fiscal_date_yd = date_data.tm_yday
        instance.fiscal_date_q = quarter(instance.fiscal_date.date())
        instance.fiscal_date_m = date_data.tm_mon
        instance.fiscal_date_md = date_data.tm_mday
        instance.fiscal_date_w = week_of_year(instance.fiscal_date.date())
        instance.fiscal_date_wd = date_data.tm_wday
        instance.fiscal_date_yq = "{year}-Q{quarter}".\
            format(year=instance.fiscal_date_y,
                   quarter=instance.fiscal_date_q)
        instance.fiscal_date_ym = "{year}-{month:02d}".\
            format(year=instance.fiscal_date_y,
                   month=instance.fiscal_date_m)
    else:
        instance.fiscal_date_y = None
        instance.fiscal_date_yd = None
        instance.fiscal_date_q = None
        instance.fiscal_date_m = None
        instance.fiscal_date_md = None
        instance.fiscal_date_w = None
        instance.fiscal_date_wd = None
        instance.fiscal_date_yq = None
        instance.fiscal_date_ym = None


DFP_FINANCIAL_INFO_INSTANT = "INSTANT"  # Individual
DFP_FINANCIAL_INFO_DURATION = "DURATION"  # Consolidated
FINANCIAL_INFO_TYPES = [DFP_FINANCIAL_INFO_INSTANT,
                        DFP_FINANCIAL_INFO_DURATION]

DFP_BALANCE_INVALID = "INVALID"
DFP_BALANCE_IF = "IF"  # ??
DFP_BALANCE_BPA = "ASSETS"  # Balanços Patrimoniais Activos
DFP_BALANCE_BPP = "LIABILITIES"  # Balanços Patrimoniais Passivo
DFP_BALANCE_DRE = "DRE"  # Demonstrativo de Resultados
DFP_BALANCE_DRA = "DRA"  # Demonstraçao do Resultado Abrangente
DFP_BALANCE_DFC_MD = "DFC_MD"  # Demonstrativo Fluxo de Caixa - Método Direto
DFP_BALANCE_DFC_MI = "DFC_MI"  # Demonstrativo Fluxo de Caixa - Método Indireto
DFP_BALANCE_DMPL = "DMPL"  # Demonstraçao das Mutaçoes do Patrimônio Líquido
DFP_BALANCE_DVA = "DVA"  # Demonstraçao Valor Adicionado

BALANCE_TYPES = [
    DFP_BALANCE_INVALID,    # 0
    DFP_BALANCE_IF,         # 1
    DFP_BALANCE_BPA,        # 2
    DFP_BALANCE_BPP,        # 3
    DFP_BALANCE_DRE,        # 4
    DFP_BALANCE_DRA,        # 5
    DFP_BALANCE_DFC_MD,     # 6
    DFP_BALANCE_DFC_MI,     # 7
    DFP_BALANCE_DMPL,       # 8
    DFP_BALANCE_DVA         # 9
]


class BovespaAccount(CustomDjangoCassandraModel):

    __table_name__ = "bovespa_account"

    # ID of the company in B3
    ccvm = columns.Text(partition_key=True)

    # Date of the account value
    period = columns.Date(primary_key=True, clustering_order="DESC")

    # The account number. Ex. "1.01.01"
    number = columns.Text(primary_key=True, max_length=15)

    # Financial type account (instant/individual or consolidated)
    financial_info_type = columns.Text(primary_key=True, max_length=15)

    # Type of financial statement
    balance_type = columns.Text(max_length=15, required=True)

    # The account name. Ex. "Receita de Venda de Bens e/ou Serviços"
    name = columns.Text(max_length=200, required=True)

    # The value of the account
    value = columns.Decimal(required=True)

    # The comments. Used for "DFP_BALANCE_DMPL" accounts, explaining the
    # meaning of the account: Shareholder's Equity, Accrued Profit/Loss, etc.
    comments = columns.Text()

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)
    deleted_reason = columns.Text()

    class Meta:
        get_pk_field = "ccvm"

    def validate(self):
        super().validate()

        if self.financial_info_type not in FINANCIAL_INFO_TYPES:
            raise ValidationError(
                "Invalid financial type [{0}] for account "
                "[{1} {2}]. Valid types are: {3}.".
                format(self.financial_info_type,
                       self.number,
                       self.name,
                       FINANCIAL_INFO_TYPES))

        if self.balance_type not in BALANCE_TYPES:
            raise ValidationError(
                "Invalid balance type [{0}]. Valid types are: {1}.".
                format(self.balance_type, BALANCE_TYPES))


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=BovespaAccount)
def pre_save_bovespa_account(
        sender, instance=None, using=None, update_fields=None, **kwargs):
    instance.updated_at = datetime.utcnow()
