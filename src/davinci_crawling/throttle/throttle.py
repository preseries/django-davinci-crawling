# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

# https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
from abc import ABC, abstractmethod
from datetime import timedelta
from functools import wraps
import importlib

from davinci_crawling.utils import get_class_from_name
from django.conf import settings

DEFAULT_THROTTLE_MANAGER = \
    "davinci_crawling.throttle.memory_throttle.MemoryThrottle"


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
    manager = None

    def __init__(self, crawler_name, seconds=1, minutes=0, hours=0, rate=10,
                 max_tokens=10, throttle_suffix_field=None):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.rate = rate
        self.max_tokens = max_tokens
        self.crawler_name = crawler_name
        self.suffix_field = throttle_suffix_field

    def get_throttle_manager(self):
        if not self.manager:
            if hasattr(settings, 'DAVINCI_CONF') and \
                    "throttle" in settings.DAVINCI_CONF["architecture-params"]\
                    and "implementation" in settings.DAVINCI_CONF[
                    "architecture-params"]["throttle"]:
                throttle_implementation = settings.DAVINCI_CONF[
                    "architecture-params"]["throttle"]["implementation"]
            else:
                throttle_implementation = DEFAULT_THROTTLE_MANAGER

            manager_clazz = get_class_from_name(throttle_implementation)

            self.manager = manager_clazz(
                self.crawler_name, seconds=self.throttle_period.seconds,
                rate=self.rate, max_tokens=self.max_tokens)

        return self.manager

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            throttle_suffix = None
            if self.suffix_field:
                throttle_suffix = kwargs.get(self.suffix_field)

            manager = self.get_throttle_manager()

            if throttle_suffix:
                throttle_key = "%s_%s_%s" % (manager.crawler_name,
                                             fn.__name__,
                                             throttle_suffix)
            else:
                throttle_key = "%s_%s" % (manager.crawler_name,
                                          fn.__name__)
            manager.wait_for_token(throttle_key)
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
