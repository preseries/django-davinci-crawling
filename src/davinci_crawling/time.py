# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import dateutil.parser
import time


def mk_datetime(datetime_str):
    """
    Process ISO 8661 date time formats https://en.wikipedia.org/wiki/ISO_8601
    """
    return dateutil.parser.parse(datetime_str)


def milliseconds(datetime_val):
    epoch = time.mktime(datetime_val.timetuple()) + \
        (datetime_val.microsecond / 1000000.)
    return int(round((float('%f' % epoch) * 1000)))
