# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging
import calendar
import xlsxwriter
from datetime import datetime, date

from solrq import Q
from caravaggio_rest_api.utils import quarter
from caravaggio_rest_api.haystack.backends.utils import \
    CaravaggioSearchPaginator

from django.core.management import BaseCommand

from davinci_crawling.example.bovespa.models import \
    BovespaAccount, FINANCIAL_INFO_TYPES, \
    DFP_FINANCIAL_INFO_INSTANT, DFP_FINANCIAL_INFO_DURATION, \
    DFP_BALANCE_BPA, DFP_BALANCE_BPP, \
    DFP_BALANCE_DRE, DFP_BALANCE_DRA, DFP_BALANCE_DFC_MD, DFP_BALANCE_DFC_MI, \
    DFP_BALANCE_DVA, DFP_BALANCE_IF
from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from davinci_crawling.time import mk_datetime

_logger = logging.getLogger(
    "davinci_crawler_{}.commands.gen_finstat".
    format(BOVESPA_CRAWLER))

MONTHS_PER_QUARTER = [3, 6, 9, 12]

accounts_data_cache = {}


def get_quarter_date(period, accumulated=False):
    """
    Returns end of the quarter associated to the informed period
    :param period: a date
    :return: the end date of the quarter associated to the period
    """
    if not accumulated:
        period_quarter = quarter(period)
        month = MONTHS_PER_QUARTER[period_quarter - 1]
        return date(
            period.year,
            month,
            calendar.monthrange(period.year, month)[1])
    else:
        periods = []

        period_quarter = quarter(period)
        month_per_quarter = [3, 6, 9, 12]
        month = month_per_quarter[period_quarter - 1]
        while True:
            new_period = \
                date(
                    period.year,
                    month,
                    calendar.monthrange(period.year, month)[1])
            periods.append(new_period)

            if period_quarter == 1:
                break

            period_quarter -= 1
            month = month_per_quarter[period_quarter - 1]
        return periods


def get_q4_prev_period(period, accumulated=False):
    """
    Returns the previous period (quarter) given a date. If the period is part
    of the first quarter non previous quarter is returned.
    :param period: a date
    :return: the previous quarter or null if the period is part of the
             first quarter
    """
    return date(
        period.year - 1, 12, calendar.monthrange(period.year - 1, 12)[1])


def get_prev_quarter_date(period):
    """
    Returns the previous period (quarter) given a date. If the period is part
    of the first quarter non previous quarter is returned.
    :param period: a date
    :return: the previous quarter or null if the period is part of the
             first quarter
    """
    period_quarter = quarter(period)
    if period_quarter == 1:
        return

    previous_quarter = period_quarter - 1 if period_quarter > 1 else 4

    month_per_quarter = [3, 6, 9, 12]

    year = period.year if period_quarter > 1 else period.year - 1
    month = month_per_quarter[previous_quarter - 1]

    return date(year, month, calendar.monthrange(year, month)[1])


def get_same_quarter_prev_period(period, accumulated=False):
    """
    Returns the previous period (quarter) given a date. If the period is part
    of the first quarter non previous quarter is returned.
    :param period: a date
    :param accumulated: if we want all the dates from
                    the start of the prev year until the quarter
    :return: the previous quarter or null if the period is part of the
             first quarter
    """
    if not accumulated:
        period_quarter = quarter(period)
        month_per_quarter = [3, 6, 9, 12]
        month = month_per_quarter[period_quarter - 1]

        return date(period.year - 1,
                    month,
                    calendar.monthrange(period.year - 1, month)[1])
    else:
        periods = []

        period_quarter = quarter(period)
        month_per_quarter = [3, 6, 9, 12]
        month = month_per_quarter[period_quarter - 1]
        while True:
            new_period = \
                date(period.year - 1,
                     month,
                     calendar.monthrange(period.year - 1, month)[1])
            periods.append(new_period)

            if period_quarter == 1:
                break

            period_quarter -= 1
            month = month_per_quarter[period_quarter - 1]
        return periods


def get_closest_fiscal_date(ccvm, period):

    closest_account = BovespaAccount.objects.filter(
        ccvm=ccvm, period__lte=period).\
        order_by('-period').limit(1).get()
    return closest_account.period.date()


PERIODS_BY_BALANCE_TYPE = (
    (DFP_BALANCE_BPA,
     ("Active",
      # Other periods to compare with
      (("End Prev. Exercise", get_q4_prev_period, False),),
      # Percentages - Comparisons. 1 = current period, 2 first of other periods
      (("Evolution", (1, 2)),))),
    (DFP_BALANCE_BPP,
     ("Passive",
      # Other periods to compare with
      (("End Prev. Exercise", get_q4_prev_period, False),),
      # Percentages - Comparisons. 1 = current period, 2 first of other periods
      (("Evolution", (1, 2)),))),
    (DFP_BALANCE_DRE,
     ("Income (DRE)",
      # Other periods to compare with (True/False for accumulated or not)
      (
          ("Accum. Year", get_quarter_date, True),
          ("Quarter Prev. Exercise", get_same_quarter_prev_period, False),
          ("Accum. Prev. Exercise", get_same_quarter_prev_period, True),
      ),
      # Percentages - Comparisons. 1 = current period, 2 first of other periods
      (
          ("Quarter Evolution", (1, 3)),
          ("Accum. Evolution", (2, 4)),
       ))),
    (DFP_BALANCE_DRA,
     ("Comprehensive (DRA)",
      # Other periods to compare with
      (
          ("Accum. Year", get_quarter_date, True),
          ("Quarter Prev. Exercise", get_same_quarter_prev_period, False),
          ("Accum. Prev. Exercise", get_same_quarter_prev_period, True),
      ),
      # Percentages - Comparisons. 1 = current period, 2 first of other periods
      (
          ("Quarter Evolution", (1, 3)),
          ("Accum. Evolution", (2, 4)),
      ))),
    (DFP_BALANCE_DFC_MD,
     ("Cash-flow",
      # Other periods to compare with
      (("Accum Prev. Exercise", get_same_quarter_prev_period, False),),
      # Percentages - Comparisons. 1 = current period, 2 first of other periods
      (("Evolution", (1, 2)),))),
    (DFP_BALANCE_DFC_MI,
     ("Cash-flow",
      # Other periods to compare with
      (("Accum. Prev. Exercise", get_same_quarter_prev_period, False),),
      # Percentages - Comparisons. 1 = current period, 2 first of other periods
      (("Evolution", (1, 2)),))),
    (DFP_BALANCE_DVA,
     ("Added value (DVA)",
      # Other periods to compare with
      (("Accum. Prev. Exercise", get_same_quarter_prev_period, False),),
      # Percentages - Comparisons. 1 = current period, 2 first of other periods
      (("Evolution", (1, 2)),))),
)

trans = {
    DFP_BALANCE_BPA: "Balance sheet assets (BPA)",
    DFP_BALANCE_BPP: "Balance sheet liabilities (BPP)",
    DFP_BALANCE_DRE: "Income statement (DRE)",
    DFP_BALANCE_DRA: "Comprehensive Income (DRA)",
    DFP_BALANCE_DFC_MD: "Cash-flow",
    DFP_BALANCE_DFC_MI: "Cash-flow",
    DFP_BALANCE_DVA: "Added value",
    # DFP_BALANCE_DMPL: "Added value",
}


def load_accounts(ccvm, period):
    key = "{ccvm}_{period:%Y%m%d}".format(ccvm=ccvm, period=period)
    period_data = accounts_data_cache.get(key, None)

    if not period_data:
        period_data = {}
        # Get all the company accounts for the given
        # company and fiscal_date
        filter = Q(period=period) & Q(ccvm=ccvm)

        _logger.debug("Loading from database the accounts for {} - {}...".
                      format(ccvm, str(filter)))
        paginator = CaravaggioSearchPaginator(
            query_string=str(filter),
            limit=5000, max_limit=5000). \
            models(BovespaAccount). \
            select("number", "name",
                   "financial_info_type", "balance_type", "comments",
                   "value")

        while paginator.has_next():
            _logger.debug(
                "{0}/{1} accounts loaded from database...".
                format(paginator.get_loaded_docs(),
                       paginator.get_hits()))
            paginator.next()
            for d in paginator.get_results():
                balance_type_accounts = \
                    period_data.setdefault(d.balance_type, {})
                financial_type_accounts = balance_type_accounts.\
                    setdefault(d.financial_info_type, {})

                financial_type_accounts[d.number] = {
                    "number": d.number,
                    "name": d.name,
                    "comments": d.comments,
                    "financial_info_type": d.financial_info_type,
                    "balance_type": d.balance_type,
                    "value": float(d.value)}
        accounts_data_cache[key] = period_data

    return period_data


def add_basic_indicators(
        workbook, format_title=None, format_header=None,
        format_money=None, format_percent=None, format_stock_price=None):

    worksheet = workbook.add_worksheet(name="Basic Indicators")

    worksheet.set_column(0, 0, 45)
    worksheet.set_column(1, 100, 20)

    row = 0
    for info_type in FINANCIAL_INFO_TYPES:
        acc_type = "" if info_type == DFP_FINANCIAL_INFO_INSTANT else "c"
        indicators_type = "Individual" \
            if info_type == DFP_FINANCIAL_INFO_INSTANT else "Consolidated"

        worksheet.write(
            row + 0, 0, "{} Indicators".format(indicators_type), format_title)

        worksheet.write(row + 1, 0, "Market Cap", format_header)
        worksheet.write(
            row + 1, 1,
            '=VLOOKUP("3.99.99.22",\'Income (DRE)\'!A1:C10000,3,0)*'
            'VLOOKUP("3.99.99.30",\'Income (DRE)\'!A1:C10000,3,0)'.
            format(acc_type), format_money)

        worksheet.write(row + 4, 0, "Operational efficiency", format_header)
        worksheet.write(row + 4, 1, "Current Quarter", format_header)
        worksheet.write(row + 4, 2, "Accum. Year", format_header)
        worksheet.write(row + 4, 3, "Quarter Prev. Year", format_header)
        worksheet.write(row + 4, 4, "Accum. Prev. Year", format_header)

        worksheet.write(row + 5, 0, "Gross Margin")
        worksheet.write(
            row + 5, 1,
            '=VLOOKUP("3.03{0}",\'Income (DRE)\'!A1:C10000,3,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,3,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 5, 2,
            '=VLOOKUP("3.03{0}",\'Income (DRE)\'!A1:F10000,4,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,4,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 5, 3,
            '=VLOOKUP("3.03{0}",\'Income (DRE)\'!A1:F10000,5,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,5,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 5, 4,
            '=VLOOKUP("3.03{0}",\'Income (DRE)\'!A1:F10000,6,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,6,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 6, 0, "EBIT Margin")
        worksheet.write(
            row + 6, 1,
            '=VLOOKUP("3.05{0}",\'Income (DRE)\'!A1:C10000,3,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 6, 2,
            '=VLOOKUP("3.05{0}",\'Income (DRE)\'!A1:F10000,4,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,4,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 6, 3,
            '=VLOOKUP("3.05{0}",\'Income (DRE)\'!A1:F10000,5,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,5,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 6, 4,
            '=VLOOKUP("3.05{0}",\'Income (DRE)\'!A1:F10000,6,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,6,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 7, 0, "Net Margin")
        worksheet.write(
            row + 7, 1,
            '=VLOOKUP("3.11{0}",\'Income (DRE)\'!A1:C10000,3,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 7, 2,
            '=VLOOKUP("3.11{0}",\'Income (DRE)\'!A1:F10000,4,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,4,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 7, 3,
            '=VLOOKUP("3.11{0}",\'Income (DRE)\'!A1:F10000,5,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,5,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 7, 4,
            '=VLOOKUP("3.11{0}",\'Income (DRE)\'!A1:F10000,6,0)/'
            'VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:F10000,6,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 8, 0, "ROE")
        worksheet.write(
            row + 8, 1,
            '=VLOOKUP("3.11{0}",\'Income (DRE)\'!A1:D10000,4,0)/B2'.
            format(acc_type), format_percent)

        worksheet.write(row + 9, 0, "Annualized ROE")
        worksheet.write(
            row + 9, 1,
            '=4*VLOOKUP("3.11{0}",\'Income (DRE)\'!A1:C10000,3,0)/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 10, 0, "Annualized EBIT/Assets")
        worksheet.write(
            row + 10, 1,
            '=4*VLOOKUP("3.05{0}",\'Income (DRE)\'!A1:C10000,3,0)/'
            'VLOOKUP("1{0}",\'Active\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 11, 0, "Annualized RL/Assets")
        worksheet.write(
            row + 11, 1,
            '=4*VLOOKUP("3.01{0}",\'Income (DRE)\'!A1:C10000,3,0)/'
            'VLOOKUP("1{0}",\'Active\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 13, 0, "Price indicators", format_header)

        worksheet.write(row + 14, 0, "Price Earnings Ratio (PER)")
        worksheet.write(
            row + 14, 1,
            '=(VLOOKUP("3.99.99.22",\'Income (DRE)\'!A1:C10000,3,0)*'
            'VLOOKUP("3.99.99.30",\'Income (DRE)\'!A1:C10000,3,0))/'
            '(4*VLOOKUP("3.11{0}",\'Income (DRE)\'!A1:C10000,3,0))'.
            format(acc_type), format_stock_price)

        worksheet.write(row + 15, 0, "Price per Book Value (P/BV)")
        worksheet.write(
            row + 15, 1,
            '=(VLOOKUP("3.99.99.22",\'Income (DRE)\'!A1:C10000,3,0)*'
            'VLOOKUP("3.99.99.30",\'Income (DRE)\'!A1:C10000,3,0))/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:C10000,3,0)'.
            format(acc_type), format_stock_price)

        worksheet.write(row + 16, 0, "Enterprise Value per EBIT (EV/EBIT)")
        worksheet.write(
            row + 16, 1,
            '=(VLOOKUP("3.99.99.22",\'Income (DRE)\'!A1:C10000,3,0)*'
            'VLOOKUP("3.99.99.30",\'Income (DRE)\'!A1:C10000,3,0))/'
            '(4*VLOOKUP("3.05{0}",\'Income (DRE)\'!A1:C10000,3,0))'.
            format(acc_type), format_stock_price)

        worksheet.write(row + 18, 0, "Debt indicators", format_header)
        worksheet.write(row + 18, 1, "Current Quarter", format_header)
        worksheet.write(row + 18, 2, "End Prev. Exercise", format_header)

        worksheet.write(row + 19, 0, "Loans / Equity (L/E ratio)")
        worksheet.write(
            row + 19, 1,
            '=(IFERROR(VLOOKUP("2.01.04{0}",\'Passive\'!A1:C10000,3,0), 0.0)+'
            'IFERROR(VLOOKUP("2.02.01{0}",\'Passive\'!A1:C10000,3,0), 0.0))/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 19, 2,
            '=(IFERROR(VLOOKUP("2.01.04{0}",\'Passive\'!A1:D10000,4,0), 0.0)+'
            'IFERROR(VLOOKUP("2.02.01{0}",\'Passive\'!A1:D10000,4,0), 0.0))/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:D10000,4,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 20, 0, "Total Debt / Equity (D/E)")
        worksheet.write(
            row + 20, 1,
            '=(VLOOKUP("2.01{0}",\'Passive\'!A1:C10000,3,0)+'
            'VLOOKUP("2.02{0}",\'Passive\'!A1:C10000,3,0))/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 20, 2,
            '=(VLOOKUP("2.01{0}",\'Passive\'!A1:D10000,4,0)+'
            'VLOOKUP("2.02{0}",\'Passive\'!A1:D10000,4,0))/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:D10000,4,0)'.
            format(acc_type), format_percent)

        worksheet.write(row + 21, 0, "Long Term Debt / Equity (LTD/E)")
        worksheet.write(
            row + 21, 1,
            '=VLOOKUP("2.02{0}",\'Passive\'!A1:C10000,3,0)/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:C10000,3,0)'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 21, 2,
            '=VLOOKUP("2.02{0}",\'Passive\'!A1:D10000,4,0)/'
            'VLOOKUP("2.03{0}",\'Passive\'!A1:D10000,4,0)'.
            format(acc_type), format_percent)

        worksheet.write(
            row + 22, 0,
            "Current Liabilities / Total Debt (Financial Indebtedness)")
        worksheet.write(
            row + 22, 1,
            '=IFERROR(VLOOKUP("2.01{0}",\'Passive\'!A1:C10000,3,0), 0.0)/'
            '(IFERROR(VLOOKUP("2.01{0}",\'Passive\'!A1:C10000,3,0), 0.0)+'
            'IFERROR(VLOOKUP("2.02{0}",\'Passive\'!A1:C10000,3,0), 0.0))'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 22, 2,
            '=IFERROR(VLOOKUP("2.01{0}",\'Passive\'!A1:D10000,4,0), 0.0)/'
            '(IFERROR(VLOOKUP("2.01{0}",\'Passive\'!A1:D10000,4,0), 0.0)+'
            'IFERROR(VLOOKUP("2.02{0}",\'Passive\'!A1:D10000,4,0), 0.0))'.
            format(acc_type), format_percent)

        worksheet.write(row + 23, 0, "Long Term Debt / Total Debt")
        worksheet.write(
            row + 23, 1,
            '=IFERROR(VLOOKUP("2.02{0}",\'Passive\'!A1:C10000,3,0), 0.0)/'
            '(IFERROR(VLOOKUP("2.01{0}",\'Passive\'!A1:C10000,3,0), 0.0)+'
            'IFERROR(VLOOKUP("2.02{0}",\'Passive\'!A1:C10000,3,0), 0.0))'.
            format(acc_type), format_percent)
        worksheet.write(
            row + 23, 2,
            '=IFERROR(VLOOKUP("2.02{0}",\'Passive\'!A1:D10000,4,0), 0.0)/'
            '(IFERROR(VLOOKUP("2.01{0}",\'Passive\'!A1:D10000,4,0), 0.0)+'
            'IFERROR(VLOOKUP("2.02{0}",\'Passive\'!A1:D10000,4,0), 0.0))'.
            format(acc_type), format_percent)

        worksheet.write(row + 24, 0, "Quick Ratio")
        worksheet.write(
            row + 24, 1,
            '=(IFERROR(VLOOKUP("1.01.01{0}",\'Active\'!A1:C10000,3,0), 0.0)+'
            'IFERROR(VLOOKUP("1.01.02{0}",\'Active\'!A1:C10000,3,0), 0.0)+'
            'IFERROR(VLOOKUP("1.01.03{0}",\'Active\'!A1:C10000,3,0), 0.0))/'
            'VLOOKUP("2.01{0}",\'Passive\'!A1:C10000,3,0)'.
            format(acc_type), format_stock_price)
        worksheet.write(
            row + 24, 2,
            '=(IFERROR(VLOOKUP("1.01.01{0}",\'Active\'!A1:D10000,4,0), 0.0)+'
            'IFERROR(VLOOKUP("1.01.02{0}",\'Active\'!A1:D10000,4,0), 0.0)+'
            'IFERROR(VLOOKUP("1.01.03{0}",\'Active\'!A1:D10000,4,0), 0.0))/'
            'VLOOKUP("2.01{0}",\'Passive\'!A1:D10000,4,0)'.
            format(acc_type), format_stock_price)

        # worksheet.write(
        #   row + 25, 0, "Accum. Interest / Gross Debt End Exercise")
        # worksheet.write(
        #   row + 25, 1,
        #   '=VLOOKUP("7.08.03.01{0}",\'Added value (DVA)\'!A1:C10000,3,0)/
        #   (IFERROR(VLOOKUP("2.01.04{0}",\'Passive\'!A1:D10000,4,0), 0.0)+
        #   IFERROR(VLOOKUP("2.02.01{0}",\'Passive\'!A1:D10000,4,0), 0.0))'.
        #   format(acc_type), format_percent)
        # worksheet.write(
        #   row + 25, 2,
        #   '=VLOOKUP("7.08.03.01{0}",\'Added value (DVA)\'!A1:D10000,4,0)/
        #   (IFERROR(VLOOKUP("2.01.04{0}",\'Passive\'!A1:D10000,4,0), 0.0)+
        #   IFERROR(VLOOKUP("2.02.01{0}",\'Passive\'!A1:D10000,4,0), 0.0))'.
        #   format(acc_type), format_percent)

        row += 26


def export_data(ccvm, current_period):
    workbook = xlsxwriter.Workbook(
        "{0}_{1:%Y%m%d}.xlsx".format(ccvm, current_period))

    # Formats

    # Add a text format for the titles
    bold = workbook.add_format({'bold': True})
    bold.set_font_size(20)

    # Add a text format for the headers
    bold_header = workbook.add_format({'bold': True})
    bold_header.set_font_size(15)

    # Add a number format for cells with money.
    money = workbook.add_format({'num_format': '#,##0'})

    stock_price = workbook.add_format({'num_format': '0.00'})

    # Add a percent format for cells with percentages.
    percent = workbook.add_format({'num_format': '0.00%'})

    for balance_type_info in PERIODS_BY_BALANCE_TYPE:
        balance_type = balance_type_info[0]
        sheet_name = balance_type_info[1][0]
        other_periods = balance_type_info[1][1]
        other_periods_evol = balance_type_info[1][2]

        _logger.debug("Processing {0} for period {1:%Y-%m-%d}".
                      format(balance_type, current_period))

        current_period_data = load_accounts(ccvm, current_period)

        if balance_type not in current_period_data:
            continue

        worksheet = workbook.add_worksheet(name=sheet_name)

        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 40)
        worksheet.set_column(2, 100, 15)

        row = 0
        for info_type in FINANCIAL_INFO_TYPES:

            if info_type not in current_period_data[balance_type]:
                continue

            # Instant data
            current_instant_data = current_period_data[
                balance_type][info_type]

            accounts = {}
            accounts.update(
                {acc_number: current_instant_data[acc_number]["name"]
                 for acc_number in current_instant_data.keys()})

            # Add periods accounts
            for period_name, period_func, accumulated in other_periods:
                other_period_dates = period_func(
                    current_period, accumulated=accumulated)
                other_period_dates = [other_period_dates] \
                    if not isinstance(other_period_dates, (list, tuple)) \
                    else other_period_dates
                for other_period_date in other_period_dates:
                    other_period_data = load_accounts(ccvm, other_period_date)

                    _logger.debug(
                        "Processing {0} for other period {1} - {2:%Y-%m-%d}".
                        format(balance_type, period_name, other_period_date))

                    data = other_period_data[balance_type][info_type]

                    accounts.update(
                        {acc_number: data[acc_number]["name"]
                         for acc_number in data.keys()})

            subsection_tittle = "Individual" \
                if info_type == DFP_FINANCIAL_INFO_INSTANT else "Consolidated"
            worksheet.write(row + 0, 0, "{0} details: {1}".
                            format(subsection_tittle,
                                   trans[balance_type]),
                            bold)

            worksheet.write(row + 1, 0, "Account", bold_header)
            worksheet.write(row + 1, 1, "Description", bold_header)
            worksheet.write(row + 1, 2, "Current Quarter", bold_header)
            for index, (period_name, period_func, accumulated) \
                    in enumerate(other_periods):
                worksheet.write(
                    row + 1, 2 + index + 1, period_name, bold_header)

            for index, (evol_name, period_indexes) in \
                    enumerate(other_periods_evol):
                worksheet.write(
                    row + 1, 2 + len(other_periods) + index + 1,
                    evol_name,
                    bold_header)

            row += 2
            for acc_number, acc_name in accounts.items():
                current_period_value = \
                    current_instant_data[acc_number]["value"] \
                    if acc_number in current_instant_data else 0.0

                other_period_values = []
                for period_name, period_func, accumulated in other_periods:
                    other_period_dates = \
                        period_func(current_period, accumulated=accumulated)

                    other_period_dates = [other_period_dates] \
                        if not isinstance(other_period_dates, (list, tuple)) \
                        else other_period_dates

                    value = 0.0
                    for other_period_date in other_period_dates:
                        other_period_data = \
                            load_accounts(ccvm, other_period_date)
                        data = other_period_data[balance_type][info_type]
                        value += data[acc_number]["value"] \
                            if acc_number in data else 0.0

                    other_period_values.append(value)

                    # other_period_date = period_func(current_period)
                    # other_period_data = \
                    #    load_accounts(ccvm, other_period_date)
                    # data = other_period_data[balance_type][info_type]
                    # other_period_values.append(
                    #    data[acc_number]["value"]
                    #    if acc_number in data else 0.0)

                # We continue with the next account if we do not have value
                # in the current period and eny of the other periods to
                # compare with, we continue with the next account
                if current_period_value == 0 and not all(other_period_values):
                    continue

                acc_number = acc_number \
                    if info_type == DFP_FINANCIAL_INFO_INSTANT \
                    else "{}c".format(acc_number)

                worksheet.write(row, 0, acc_number)
                worksheet.write(row, 1, acc_name)
                worksheet.write(row, 2, current_period_value, money)
                for index, period_value in enumerate(other_period_values):
                    worksheet.write(row, 2 + index + 1,
                                    period_value,
                                    money)

                for index, (evol_name, period_indexes) in \
                        enumerate(other_periods_evol):
                    total_col_inbtw = \
                        1 + len(other_periods) + index + 1
                    indexes = [period_index - total_col_inbtw
                               for period_index in period_indexes]
                    worksheet.write(
                        row, 2 + len(other_periods) + index + 1,
                        '=(INDIRECT("RC[{0}]",0)-INDIRECT("RC[{1}]",0))/'
                        'INDIRECT("RC[{1}]",0)'.format(*indexes),
                        percent)

                row += 1

            # Let's add the shares information
            shares_start_row = row
            if balance_type == DFP_BALANCE_DRE:
                shares_data = current_period_data[
                    DFP_BALANCE_IF][DFP_FINANCIAL_INFO_DURATION]
                ordinary_shares = shares_data["1.89.01"]["value"]
                preferred_shares = shares_data["1.89.02"]["value"]
                total_shares = shares_data["1.89.03"]["value"]
                ordinary_shares_in_treasury = shares_data["1.89.04"]["value"]
                preferred_shares_in_treasury = shares_data["1.89.05"]["value"]
                total_shares_in_treasury = shares_data["1.89.06"]["value"]

                worksheet.write(row, 0, "3.99.99.10")
                worksheet.write(row, 1, "Ordinary shares in treasury")
                worksheet.write(row, 2, ordinary_shares_in_treasury, money)
                row += 1

                worksheet.write(row, 0, "3.99.99.11")
                worksheet.write(row, 1, "Preferred shares in treasury")
                worksheet.write(row, 2, preferred_shares_in_treasury, money)
                row += 1

                worksheet.write(row, 0, "3.99.99.12")
                worksheet.write(row, 1, "Total shares in treasury")
                worksheet.write(row, 2, total_shares_in_treasury, money)
                row += 1

                worksheet.write(row, 0, "3.99.99.20")
                worksheet.write(row, 1, "Ordinary shares")
                worksheet.write(row, 2, ordinary_shares, money)
                row += 1

                worksheet.write(row, 0, "3.99.99.21")
                worksheet.write(row, 1, "Preferred shares")
                worksheet.write(row, 2, preferred_shares, money)
                row += 1

                worksheet.write(row, 0, "3.99.99.22")
                worksheet.write(row, 1, "Total shares")
                worksheet.write(row, 2, total_shares, money)
                row += 1

                worksheet.write(row, 0, "3.99.99.30")
                worksheet.write(row, 1, "Stock price")
                worksheet.write(row, 2, 0.0, stock_price)
                row += 1

    add_basic_indicators(workbook,
                         format_title=bold,
                         format_header=bold_header,
                         format_money=money,
                         format_percent=percent,
                         format_stock_price=stock_price)

    workbook.close()


class Command(BaseCommand):
    help = 'Generate the company financial statements'

    def add_arguments(self, parser):
        # The company to process
        parser.add_argument(
            '--company-ccvm',
            required=True,
            type=str,
            action='store',
            default=None,
            dest='company_ccvm',
            help="The CCVM code of the company"
                 " Ex. 9512 (PETROBRAS)")
        # The fiscal date to be used for the generation
        parser.add_argument(
            '--fiscal-date',
            required=False,
            action='store',
            dest='fiscal_date',
            default=datetime.utcnow(),
            type=mk_datetime,
            help="The fiscal date to use to generate the financial statements."
                 "We are going to round the date to the nearest quarter "
                 "date after or equals the given date. For instance, "
                 "2018-09-10 will round to 2018-09-30 that is the end date "
                 "of the Q3 for 2018."
                 " Ex. '2018-09-30")

    def handle(self, *args, **options):
        try:
            ccvm = options.get("company_ccvm")
            fiscal_date = options.get("fiscal_date")

            current_period = get_closest_fiscal_date(ccvm, fiscal_date)
            _logger.debug(
                "Loading period data: {:%Y-%m-%d}".
                format(current_period))
            # current_period_data = load_accounts(ccvm, current_period)

            # q4_prev_period = get_q4_prev_period(current_period)
            # _logger.debug(
            #    "Loading prev Q4 period data: {:%Y-%m-%d}".
            #        format(q4_prev_period))
            # q4_prev_period_data = load_accounts(ccvm, q4_prev_period)

            export_data(ccvm, current_period)

            _logger.info("Financial statements successfully generated!")
        except Exception:
            _logger.exception("Error generating the financial statements")
