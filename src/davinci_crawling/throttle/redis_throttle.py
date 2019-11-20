# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

# https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
import logging
import time
from multiprocessing import Manager

from davinci_crawling.throttle.throttle import \
    ThrottleManager
from django.conf import settings
from pylimit import PyRateLimit

manager = Manager()
lock = manager.Lock()
_throttle_info = manager.dict()

_logger = logging.getLogger("davinci_crawling")

PyRateLimit.init(redis_host=settings.REDIS_HOST_PRIMARY,
                 redis_port=settings.REDIS_PORT_PRIMARY,
                 redis_password=settings.REDIS_PASS_PRIMARY)


class RedisThrottle(ThrottleManager):
    """
    Use redis as throttle implementation, this method will check on redis if
    we can proceed with the throttle, this way the throttle will be distributed
    instead of single machine as MemoryThrottle
    """

    def wait_for_token(self, key):
        pylimit = PyRateLimit(int(self.throttle_period.total_seconds()),
                              self.rate)

        throttle_times = 0
        current_time = int(round(time.time() * 1000000))

        while not pylimit.attempt(key, timestamp=current_time):
            throttle_times += 1
            _logger.debug("Function {} being throttle".format(key))
            time.sleep(5)

        return throttle_times
