# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from dateutil.parser import parse as date_parse

from bgds_task import CRAWLER_NAME

# A field to save in the checkpoint records
LAST_EXECUTION_DATE_CTL_FIELD = "last_execution_date"

# Crawler custom argument from_date
FROM_DATE_ARG = "from_date"

# Crawler custom argument that force to reset the from_date
# (crawl since the beginning)
RESET_FROM_DATE_ARG = "from_the_beginning"

_logger = logging.getLogger("crawler_{}".format(CRAWLER_NAME))


def get_from_date(options, checkpoint_data):
    """
    A function that returns the date the crawler should use as a date to
    start crawling.

    :param options: the parameters send to te crawler (common and custom)
    :param checkpoint_data: the dict that contains the data saved as checkpoint
    :return: the date to use as a "from date" in the crawl process
    """

    # We first get the last execution date - if exists - of the crawler.
    # This parameter is managed by the scheduler of crawlers, is not controlled
    # by the crawler itself
    from_date = options.get("last_execution_date", None)

    # Let's get - if exists - the date saved in the checkpoint record as the
    # latest date. If it exists, we replace the previous date
    # "last_execution_date" with this one
    from_date = checkpoint_data.get(
        LAST_EXECUTION_DATE_CTL_FIELD, from_date)

    # Convert the value of from_date to datetime if the date is of str type
    if isinstance(from_date, str):
        from_date = date_parse(from_date)

    # Check if the user is forcing to use a different date through the crawler
    # custom parameter with name "from_date"
    if options.get(FROM_DATE_ARG, None):
        from_date = options.get(FROM_DATE_ARG)

    # Check if the user is forcing to crawl everything again
    from_the_beginning = options.get(RESET_FROM_DATE_ARG, False)
    if from_the_beginning:
        from_date = None

    _logger.debug("From date: {}".
                  format("{0:%Y-%m-%d}".
                         format(from_date) if from_date else "BEGINNING"))

    return from_date
