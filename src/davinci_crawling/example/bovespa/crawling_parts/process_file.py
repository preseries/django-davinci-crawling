# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging
import threading

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from davinci_crawling.example.bovespa.document import load_account_details
from davinci_crawling.example.bovespa.models import \
    BovespaCompanyFile, FILE_STATUS_PROCESSED

try:
    from dse.cqlengine.query import LWTException
except ImportError:
    from cassandra.cqlengine.query import LWTException

_logger = logging.getLogger(
    "davinci_crawler_{}.crawling_part.process_file".
    format(BOVESPA_CRAWLER))


def process_file(
        options, files_to_process, ccvm_code, file_type, fiscal_date, version):

    company_file = BovespaCompanyFile.objects.get(
        ccvm=ccvm_code,
        doc_type=file_type,
        fiscal_date=fiscal_date,
        version=version)

    load_account_details(options, files_to_process, company_file)

    # The data has been loaded into the database, we can set the flag
    # of the company file to PROCESSED, we also store the thread that made the
    # job, this is used to validate the parallelism on tests.
    company_file.update(status=FILE_STATUS_PROCESSED,
                        thread_id=threading.currentThread().getName())
