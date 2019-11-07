# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

# https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
from abc import ABC, abstractmethod
from datetime import timedelta
from functools import wraps
import importlib

from django.conf import settings

DEFAULT_THROTTLE_MANAGER = "davinci_crawling.throttle.memory_throttle." \
                           "MemoryThrottle"

THROTTLE_MANAGER = None


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

    def get_throttle_manager(self):
        global THROTTLE_MANAGER
        if not THROTTLE_MANAGER:
            if hasattr(settings, 'DAVINCI_CONF') and \
                    "throttle" in settings.DAVINCI_CONF["architecture-params"]\
                    and "implementation" in settings.DAVINCI_CONF[
                    "architecture-params"]["throttle"]:
                throttle_implementation = settings.DAVINCI_CONF[
                    "architecture-params"]["throttle"]["implementation"]
            else:
                throttle_implementation = DEFAULT_THROTTLE_MANAGER

            module_name = ".".join(throttle_implementation.split('.')[:-1])
            class_name = throttle_implementation.split('.')[-1]

            module = importlib.import_module(module_name)
            THROTTLE_MANAGER = getattr(module, class_name)

        if not self.implementation:
            self.implementation = THROTTLE_MANAGER(
                self.crawler_name, seconds=self.throttle_period.seconds,
                rate=self.rate, max_tokens=self.max_tokens)
        return self.implementation

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            throttle_suffix = kwargs.get("throttle_suffix")

            implementation = self.get_throttle_manager()

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


class ThrottleManager(ABC):

    def __init__(self, crawler_name, seconds=1, minutes=0, hours=0, rate=10,
                 max_tokens=10):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.rate = rate
        self.max_tokens = max_tokens
        self.crawler_name = crawler_name

    @abstractmethod
    def wait_for_token(self, key):
        raise NotImplementedError
