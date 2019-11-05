# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

# https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
import logging
import time
from datetime import timedelta
from functools import wraps
from multiprocessing import Manager


class ThrottleImplementation(object):
    """
    Decorator that prevents a function from being called more than once every
    time period.
    To create a function that cannot be called more than 10
    requests per minute a minute:
        @throttle(minutes=1, rate=10, max_tokens=10)
        def my_fun():
            pass
    """

    def __init__(self, crawler_name, seconds=1, minutes=0, hours=0, rate=10,
                 max_tokens=10, throttle_suffix=None):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.rate = rate
        self.max_tokens = max_tokens
        self.crawler_name = crawler_name
        self.throttle_suffix = throttle_suffix

    def check_info(self, key):
        raise NotImplementedError

    def wait_for_token(self, key):
        raise NotImplementedError

    def add_new_tokens(self, key):
        raise NotImplementedError

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if self.throttle_suffix:
                throttle_key = "%s_%s_%s" % (self.crawler_name, fn.__name__,
                                             self.throttle_suffix)
            else:
                throttle_key = "%s_%s" % (self.crawler_name, fn.__name__)
            self.wait_for_token(throttle_key)
            return fn(*args, **kwargs)

        return wrapper
