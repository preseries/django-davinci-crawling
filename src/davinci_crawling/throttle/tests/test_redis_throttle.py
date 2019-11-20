# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.throttle.redis_throttle import RedisThrottle
from django.conf import settings

_logger = logging.getLogger("davinci_crawling.testing")

CHROME_OPTIONS = {
    "chromium_bin_file": settings.CHROMIUM_BIN_FILE
}


class TestRedisThrottle(CaravaggioBaseTest):
    """
    Test the proxy logic, this test requires connection with internet
    because we use the proxy mesh api and request for real pages.
    """

    all_files_count = 0

    @classmethod
    def setUpTestData(cls):
        pass

    def test_throttle(self):
        """
        Test two throttle
        """
        throttle = RedisThrottle("test", seconds=10, rate=10, max_tokens=10)
        quantity = 0
        for x in range(40):
            times_throttled = throttle.wait_for_token("test")
            # only the 10th will be throttled
            if quantity == 10:
                self.assertEqual(2, times_throttled)
                quantity = 0
            else:
                self.assertEqual(0, times_throttled)
                quantity += 1
