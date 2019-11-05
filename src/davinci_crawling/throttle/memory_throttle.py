# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

# https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
import logging
import time
from datetime import timedelta
from functools import wraps
from multiprocessing import Manager

from davinci_crawling.throttle.throttle_implementation import \
    ThrottleImplementation

manager = Manager()
lock = manager.Lock()
_throttle_info = manager.dict()

_logger = logging.getLogger("davinci_crawling")


class MemoryThrottle(ThrottleImplementation):
    """
    Decorator that prevents a function from being called more than once every
    time period.
    To create a function that cannot be called more than 10
    requests per minute a minute:
        @throttle(minutes=1, rate=10, max_tokens=10)
        def my_fun():
            pass
    """

    def check_info(self, key):
        _logger.debug("Checking tokens info for {0}".format(key))
        info = _throttle_info.get(key, None)
        if not info:
            _logger.debug("Initialize tokens for {0}".format(key))
            info = {"tokens": self.max_tokens,
                    "updated_at": time.monotonic()}
            _throttle_info[key] = info

    def wait_for_token(self, key):
        lock.acquire()
        self.check_info(key)
        while _throttle_info[key]["tokens"] <= 1:
            self.add_new_tokens(key)
            lock.release()
            _logger.debug("Function {} being throttle".format(key))
            time.sleep(5)
            lock.acquire()

        _throttle_info[key] = {
            "tokens": _throttle_info[key]["tokens"] - 1,
            "updated_at": _throttle_info[key]["updated_at"]
        }
        _logger.debug("Tokens info. {0} -> {1}".format(
            key, _throttle_info[key]))
        lock.release()

    def add_new_tokens(self, key):
        now = time.monotonic()
        time_since_update = \
            (now - _throttle_info[key]["updated_at"]) / \
            self.throttle_period.seconds
        new_tokens = int(time_since_update * self.rate)
        if new_tokens > 1:
            _throttle_info[key] = {
                "tokens": min(
                    _throttle_info[key]["tokens"] + new_tokens,
                    self.max_tokens),
                "updated_at": now
            }
            _logger.debug("New Tokens info. {0} -> {1}".format(
                key, _throttle_info[key]))