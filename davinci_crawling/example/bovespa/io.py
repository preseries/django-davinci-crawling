# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

import logging
from davinci_crawling.io import get_base_dir, mkdirs, get_local_base_dir
from davinci_crawling.example.bovespa import BOVESPA_CRAWLER

_logger = logging.getLogger("{}.io".
                            format(BOVESPA_CRAWLER))


def _doc_base_path(options, company_file):
    path = "{0}/ccvm_{1}/{2}/date_{3:%Y%m%d}_{4}".\
        format(get_base_dir(options),
               company_file.ccvm,
               company_file.doc_type,
               company_file.fiscal_date.date(),
               company_file.version).replace(".", "_")

    _logger.debug("Doc base path: {}".format(path))

    # Make sure the path exists
    mkdirs(options, "{}/".format(path))

    return path


def _doc_local_base_path(options, company_file):
    path = "{0}/ccvm_{1}/{2}/date_{3:%Y%m%d}_{4}".\
        format(get_local_base_dir(options),
               company_file.ccvm,
               company_file.doc_type,
               company_file.fiscal_date.date(),
               company_file.version).replace(".", "_")

    _logger.debug("Doc base path: {}".format(path))

    # Make sure the path exists
    mkdirs(options, "{}/".format(path))

    return path


def _doc_local_working_base_path(options, company_file):
    path = "{0}/working/ccvm_{1}/{2}/date_{3:%Y%m%d}_{4}".\
        format(get_local_base_dir(options),
               company_file.ccvm,
               company_file.doc_type,
               company_file.fiscal_date.date(),
               company_file.version).replace(".", "_")

    _logger.debug("Doc base path: {}".format(path))

    # Make sure the path exists
    mkdirs(options, "{}/".format(path))

    return path
