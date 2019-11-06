# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

# https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
from datetime import timedelta
from functools import wraps
import importlib

from django.conf import settings


class Throttle(object):
    """
    Decorator that prevents a function from being called more than once every
    time period.
    To create a function that cannot be called more than 10
    requests per minute a minute:
        @throttle(minutes=1, rate=10, max_tokens=10)
        def my_fun():
            pass
    """

    implementation = None

    def __init__(self, crawler_name, seconds=1, minutes=0, hours=0, rate=10,
                 max_tokens=10):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.rate = rate
        self.max_tokens = max_tokens
        self.crawler_name = crawler_name

    def check_info(self, key):
        raise NotImplementedError

    def wait_for_token(self, key):
        raise NotImplementedError

    def add_new_tokens(self, key):
        raise NotImplementedError

    def get_implementation(self):
        if not self.implementation:
            throttle_implementation = settings.THROTTLE_IMPLEMENTATION

            module_name = ".".join(throttle_implementation.split('.')[:-1])
            class_name = throttle_implementation.split('.')[-1]

            module = importlib.import_module(module_name)
            implementation_class = getattr(module, class_name)

            self.implementation = implementation_class(
                self.crawler_name, seconds=self.throttle_period.seconds,
                rate=self.rate, max_tokens=self.max_tokens)
        return self.implementation

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            throttle_suffix = kwargs.get("throttle_suffix")

            implementation = self.get_implementation()

            if throttle_suffix:
                throttle_key = "%s_%s_%s" % (implementation.crawler_name,
                                             fn.__name__,
                                             throttle_suffix)
            else:
                throttle_key = "%s_%s" % (implementation.crawler_name,
                                          fn.__name__)
            implementation.wait_for_token(throttle_key)
            return fn(*args, **kwargs)

        return wrapper
