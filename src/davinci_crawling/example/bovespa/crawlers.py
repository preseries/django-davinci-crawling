# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging

from caravaggio_rest_api.haystack.backends.utils import \
    CaravaggioSearchPaginator
from datetime import datetime

from dateutil.parser import parse as date_parse

from solrq import Q, Range, ANY, Value

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from davinci_crawling.example.bovespa.crawling_parts.process_file import \
    process_file
from .models import \
    BovespaCompanyFile, FILE_STATUS_NOT_PROCESSED, FILE_STATUS_ERROR

from davinci_crawling.crawler import Crawler
from davinci_crawling.io import \
    put_checkpoint_data, get_checkpoint_data, delete_all
from davinci_crawling.time import mk_datetime
from .crawling_parts.crawl_listed_companies import crawl_listed_companies
from .crawling_parts.crawl_companies_files import crawl_companies_files
from .crawling_parts.download_file import download_file

BOVESPA_FILE_CTL = BOVESPA_CRAWLER
LAST_EXECUTION_DATE_CTL_FIELD = "last_execution_date"
LAST_UPDATE_COMPANIES_LISTING_CTL_FIELD = "last_update_companies_listing"
LAST_UPDATE_COMPANIES_FILES_CTL_FIELD = "last_update_companies_files"
PROCESSED_COMPANIES_FILES_CTL_FIELD = "processed_companies_files"
COMPANIES_FILES_WITH_ERRORS_CTL_FIELD = "companies_files_w_errors"

_logger = logging.getLogger("davinci_crawler_{}".format(BOVESPA_CRAWLER))


def get_from_date(options, checkpoint_data):
    # Let's decide from which point in time we want to get the new
    # delivered company files
    from_date = options.get("last_execution_date", None)

    from_date = checkpoint_data.get(
        LAST_EXECUTION_DATE_CTL_FIELD, from_date)

    # Check if the user is forcing a different date
    if options.get("from_date", None):
        from_date = options.get("from_date")

    if isinstance(from_date, str):
        from_date = date_parse(from_date)

    # Check if the user is forcing to crawl everything again
    from_the_beginning = options.get("from_the_beginning", False)
    if from_the_beginning:
        from_date = None

    _logger.debug("From date: {}".
                  format("{0:%Y-%m-%d}".
                         format(from_date) if from_date else "BEGINNING"))

    return from_date


def get_to_date(options):
    """
    Mounts the to_date if the user specifies it on the options, this will parse
    the date to date format if it is a string.
    Args:
        options: the options object with all the options that the user added
        on command line.
    Returns: the parsed date or None if the date was not specified.
    """
    # Check if the user is forcing a to date
    to_date = options.get("to_date", None)

    if isinstance(to_date, str):
        to_date = date_parse(to_date)

    _logger.debug("To date: {}".
                  format("{0:%Y-%m-%d}".
                         format(to_date) if to_date else "END"))

    return to_date


def process_listed_companies(options, checkpoint_data, current_execution_date):
    no_update = options.get("no_update_companies_listing", False)

    # We do not want to crawl the companies listing
    if no_update:
        return

    # Parallel processing - workers
    workers_num = options.get("workers_num", 10)

    update_elapsetime = \
        options.get("companies_listing_update_elapsetime", None)

    last_update = checkpoint_data.get(
        LAST_UPDATE_COMPANIES_LISTING_CTL_FIELD, None)

    do_crawl = True if last_update is None or \
        update_elapsetime is None or \
        (last_update - current_execution_date).days > \
        update_elapsetime else False

    if do_crawl:
        crawl_listed_companies(
            options, workers_num=workers_num)


def get_not_processed_files(options, producer):
    filter = ~Q(file_url=Range(ANY, ANY)) | Q(status=FILE_STATUS_NOT_PROCESSED)

    if options.get("include_companies", None):
        filter = Q(ccvm=Value("({})".format(" ".join(
            options.get("include_companies", []))), safe=True)) & (filter)

    _logger.debug("Loading from database the files to be crawled...")
    paginator = CaravaggioSearchPaginator(
        query_string=str(filter),
        limit=1000, max_limit=1000).\
        models(BovespaCompanyFile).\
        select("ccvm", "doc_type", "fiscal_date", "version")

    while paginator.has_next():
        _logger.debug(
            "{0}/{1} files loaded from database...".
            format(paginator.get_loaded_docs(), paginator.get_hits()))
        paginator.next()
        for d in paginator.get_results():
            params = {
                "ccvm": d.ccvm,
                "doc_type": d.doc_type,
                "fiscal_date": d.fiscal_date,
                "version": d.version
            }
            producer.add_crawl_params(params, options)

    # return [file for file in
    #        CaravaggioSearchQuerySet().models(BovespaCompanyFile).
    #            raw_search(str(filter)).
    #            values_list("ccvm", "doc_type", "fiscal_date", "version")]


def process_companies_files(
        options, checkpoint_data, current_execution_date, from_date,
        to_date, producer):

    no_update = options.get("no_update_companies_files", False)

    # We do not want to crawl the companies listing
    if no_update:
        get_not_processed_files(options, producer)
        return

    update_elapsetime = \
        options.get("companies_files_update_elapsetime", None)

    last_update = checkpoint_data.get(
        LAST_UPDATE_COMPANIES_FILES_CTL_FIELD, None)

    do_crawl = True if last_update is None or \
        update_elapsetime is None or \
        (last_update - current_execution_date).days > \
        update_elapsetime else False

    if do_crawl:
        # Parallel processing - workers
        workers_num = options.get("workers_num", 10)

        # Include companies only
        include_companies = options.get("include_companies", None)

        # Get the list of files to be processed
        company_files, company_files_w_errors = crawl_companies_files(
            options,
            producer,
            workers_num=workers_num,
            include_companies=include_companies,
            from_date=from_date,
            to_date=to_date)

        processed_files = []
        if company_files and len(company_files) > 0:
            if PROCESSED_COMPANIES_FILES_CTL_FIELD in checkpoint_data:
                processed_files = checkpoint_data[
                    PROCESSED_COMPANIES_FILES_CTL_FIELD]
            processed_files.extend(company_files)
        checkpoint_data[PROCESSED_COMPANIES_FILES_CTL_FIELD] = \
            processed_files

        files_with_errors = []
        if company_files_w_errors and len(company_files_w_errors) > 0:
            if COMPANIES_FILES_WITH_ERRORS_CTL_FIELD in checkpoint_data:
                files_with_errors = checkpoint_data[
                    COMPANIES_FILES_WITH_ERRORS_CTL_FIELD]
            files_with_errors.extend(company_files_w_errors)
        checkpoint_data[COMPANIES_FILES_WITH_ERRORS_CTL_FIELD] = \
            files_with_errors

    # Let's find all the company files without file_url (not downloaded
    # and processed yet) or not processed (status)
    # get_not_processed_files(options, producer)


class BovespaCrawler(Crawler):

    __crawler_name__ = BOVESPA_CRAWLER

    def add_arguments(self, parser):
        # Process files from an specific date
        self._parser.add_argument(
            '--from-the-beginning',
            required=False,
            action='store_true',
            dest='from_the_beginning',
            default=None,
            help="Crawl all the company files."
                 "It is a way to short-circuit the global last/current dates."
                 " Ex. '2007-09-03T20:56:35.450686Z")
        # Process files from an specific date
        self._parser.add_argument(
            '--from-date',
            required=False,
            action='store',
            dest='from_date',
            default=None,
            type=mk_datetime,
            help="The date from which we want to crawl all the company files."
                 "It is a way to short-circuit the global last/current dates."
                 " Ex. '2007-09-03T20:56:35.450686Z")
        # Process files until an specific date
        self._parser.add_argument(
            '--to-date',
            required=False,
            action='store',
            dest='to_date',
            default=None,
            type=mk_datetime,
            help="The date to which we want to crawl all the company files.")
        # Crawl only the companies where the name starts with these initials
        self._parser.add_argument(
            '--crawling-initials',
            required=False,
            action='store',
            dest='crawling_initials',
            default=None,
            nargs='*',
            help="If we want to specify the initial letter of the companies"
                 "to crawl (ex A B C)")
        # Do not update the companies listing from Bovespa
        self._parser.add_argument(
            '--no-update-companies-listing',
            required=False,
            action='store_true',
            dest='no_update_companies_listing',
            help="If we do not want to update the listed companies crawling"
                 " the listing from Bovespa. We should update the list once"
                 " a month"
                 " Ex. --no-update-companies-listing")
        # Days between companies listing updates
        self._parser.add_argument(
            '--companies-listing-update-elapsetime',
            required=False,
            type=int,
            action='store',
            default=30,
            dest='companies_listing_update_elapsetime',
            help="The elapse time in days between updates of the "
                 "companies listing"
                 " Ex. 30")
        # Do not update the company files that were already persisted in the
        # database
        self._parser.add_argument(
            '--no-update-companies-files',
            required=False,
            action='store_true',
            dest='no_update_companies_files',
            help="If we want to update the file contents in the database "
                 " although the file was already downloaded in the past."
                 " Ex. --no-update-companies-files")
        # Days between companies files updates
        self._parser.add_argument(
            '--companies-files-update-elapsetime',
            required=False,
            type=int,
            action='store',
            default=30,
            dest='companies_files_update_elapsetime',
            help="The elapse time in days between updates of the "
                 "companies files."
                 " Ex. 30")
        # Do not update the companies listing from Bovespa
        self._parser.add_argument(
            '--force-download',
            required=False,
            action='store_true',
            dest='force_download',
            help="If we want to force the download of the file from "
                 " bovespa and update the permanent and local caches."
                 " Ex. --force-download")
        self._parser.add_argument(
            "--include-companies",
            action='store',
            nargs='*',
            required=False,
            dest="include_companies",
            help="If we want to focus only on a specific companies."
                 "(ex: 35 94 1384")

    def crawl_params(self, producer, **options):
        now = options.get("current_execution_date", datetime.utcnow())

        # Check if there is an internal checkpoint, use it instead of the
        # date send by the crawler system
        checkpoint_data = get_checkpoint_data(
            BOVESPA_CRAWLER, BOVESPA_FILE_CTL, default={})\

        from_date = get_from_date(options, checkpoint_data)
        to_date = get_to_date(options)

        process_listed_companies(options, checkpoint_data, now)

        process_companies_files(options, checkpoint_data, now, from_date,
                                to_date, producer)

        # Let's signal that we have processed the latest files (til 'now')
        # To process the new ones the last time we run the process
        put_checkpoint_data(BOVESPA_CRAWLER,
                            BOVESPA_FILE_CTL,
                            checkpoint_data)

    def crawl(self, task_id, crawling_params, options):
        _logger.info(
            "Processing company file [{}]".
            format(crawling_params))

        try:
            # Download the files from the source and save them into the local and
            # permanent storage for further processing.
            # It extract the files into a working folder and return the list of
            # files that can be processed
            local_file, working_local_file, files_to_process = \
                download_file(options, **crawling_params)

            # Open the files and process the content to generate the
            # BovespaCompanyNumbers with all the financial data of the company
            process_file(options, files_to_process, **crawling_params)

            # Remove cached files
            delete_all(options, local_file)
            delete_all(options, working_local_file)
        except Exception as ex:
            _logger.exception(f"Unable to process crawling task {task_id}"
                              f" with params {crawling_params}")
            BovespaCompanyFile.if_exists(
                **crawling_params).update(
                status=FILE_STATUS_ERROR)
            raise

        return "Processing company file [{}]".format(crawling_params)
