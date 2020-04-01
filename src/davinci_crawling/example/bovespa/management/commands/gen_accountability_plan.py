# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging
import xlsxwriter

from solrq import Q, Range
from caravaggio_rest_api.haystack.backends.utils import CaravaggioSearchPaginator

from django.core.management import BaseCommand

from davinci_crawling.example.bovespa.models import (
    BovespaAccount,
    DFP_BALANCE_IF,
    DFP_BALANCE_BPA,
    DFP_BALANCE_BPP,
    DFP_BALANCE_DRE,
    DFP_BALANCE_DRA,
    DFP_BALANCE_DFC_MD,
    DFP_BALANCE_DFC_MI,
    DFP_BALANCE_DMPL,
    DFP_BALANCE_DVA,
)
from davinci_crawling.example.bovespa import BOVESPA_CRAWLER

_logger = logging.getLogger("davinci_crawler_{}.commands.gen_accountability_plan".format(BOVESPA_CRAWLER))


accounts_data_cache = {}


def load_accounts(valid_account_types):
    key = "command:gen_accountability_plan:load_accounts"

    # Get all the company accounts for the given
    # company and fiscal_date
    filter = Q(value=Range(0, "*", safe=True, boundaries="exclusive"))
    balance_type_filter = None
    for balance_type in valid_account_types:
        if balance_type_filter is None:
            balance_type_filter = Q(balance_type=balance_type)
        else:
            balance_type_filter |= Q(balance_type=balance_type)

    filter = filter & (balance_type_filter)

    paginator = CaravaggioSearchPaginator(
        str(filter),
        limit=5000,
        **{"group": "true", "group.field": "number_exact", "group.limit": 1},
        useFieldCache=True
    ).models(BovespaAccount)

    accounts = {}
    while paginator.has_next():
        _logger.debug("{} accounts loaded from database...".format(paginator.get_loaded_docs()))
        paginator.next()
        for acc_number, details in paginator.get_results().items():
            accounts[acc_number] = (details[0].balance_type, details[0].name)

    return accounts


def export_accountability_plan():
    workbook = xlsxwriter.Workbook("accountability_plan.xlsx")

    # Formats

    # Add a text format for the titles
    bold = workbook.add_format({"bold": True})
    bold.set_font_size(20)

    # Add a text format for the headers
    bold_header = workbook.add_format({"bold": True})
    bold_header.set_font_size(15)

    # Add a number format for cells with money.
    money = workbook.add_format({"num_format": "#,##0"})

    # Add a percent format for cells with percentages.
    percent = workbook.add_format({"num_format": "0.00%"})

    valid_account_types = [
        DFP_BALANCE_IF,
        DFP_BALANCE_BPA,
        DFP_BALANCE_BPP,
        DFP_BALANCE_DRE,
        DFP_BALANCE_DRA,
        DFP_BALANCE_DFC_MD,
        DFP_BALANCE_DFC_MI,
        DFP_BALANCE_DMPL,
        DFP_BALANCE_DVA,
    ]

    accounts = load_accounts(valid_account_types)

    worksheets = {}

    sorted_keys = sorted(accounts.keys())
    for acc_number in sorted_keys:
        if accounts[acc_number][0] in valid_account_types:
            balance_type = accounts[acc_number][0]
            acc_name = accounts[acc_number][1]

            if balance_type not in worksheets:
                worksheet = workbook.add_worksheet(name=balance_type)
                worksheets[balance_type] = (worksheet, 0)
                row = 0
            else:
                worksheet, row = worksheets[balance_type]

            worksheet.write(row, 0, acc_number)
            worksheet.write(row, 1, acc_name)

            worksheets[balance_type] = (worksheet, row + 1)

    workbook.close()


class Command(BaseCommand):
    help = "Generate the list of unique accountability accounts " "from all the financial statements"

    def add_arguments(self, parser):
        # The company to process
        pass

    def handle(self, *args, **options):
        try:
            _logger.debug("Exporting accountability plan data...")

            export_accountability_plan()

            _logger.info("Accountability plan successfully generated!")
        except Exception:
            _logger.exception("Error generating the accountability plan")
