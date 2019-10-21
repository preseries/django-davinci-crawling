# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

# https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
import logging
import time
from datetime import timedelta
from functools import wraps
from multiprocessing import Manager

manager = Manager()
lock = manager.Lock()
_throttle_info = manager.dict()

_logger = logging.getLogger("davinci_crawling")


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

    def __init__(self, seconds=1, minutes=0, hours=0, rate=10, max_tokens=10):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.rate = rate
        self.max_tokens = max_tokens

    def check_info(self, fn_name):
        _logger.debug("Checking tokens info for {0}".format(fn_name))
        info = _throttle_info.get(fn_name, None)
        if not info:
            _logger.debug("Initialize tokens for {0}".format(fn_name))
            info = {"tokens": self.max_tokens,
                    "updated_at": time.monotonic()}
            _throttle_info[fn_name] = info

    def wait_for_token(self, fn_name):
        lock.acquire()
        self.check_info(fn_name)
        while _throttle_info[fn_name]["tokens"] <= 1:
            self.add_new_tokens(fn_name)
            lock.release()
            _logger.debug("Function {} being throttle".format(fn_name))
            time.sleep(5)
            lock.acquire()

        _throttle_info[fn_name] = {
            "tokens": _throttle_info[fn_name]["tokens"] - 1,
            "updated_at": _throttle_info[fn_name]["updated_at"]
        }
        _logger.debug("Tokens info. {0} -> {1}".format(
            fn_name, _throttle_info[fn_name]))
        lock.release()

    def add_new_tokens(self, fn_name):
        now = time.monotonic()
        time_since_update = \
            (now - _throttle_info[fn_name]["updated_at"]) / \
            self.throttle_period.seconds
        new_tokens = int(time_since_update * self.rate)
        if new_tokens > 1:
            _throttle_info[fn_name] = {
                "tokens": min(
                    _throttle_info[fn_name]["tokens"] + new_tokens,
                    self.max_tokens),
                "updated_at": now
            }
            _logger.debug("New Tokens info. {0} -> {1}".format(
                fn_name, _throttle_info[fn_name]))

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            self.wait_for_token(fn.__name__)
            return fn(*args, **kwargs)

        return wrapper
