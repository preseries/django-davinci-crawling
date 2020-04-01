# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging
import threading

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.throttle.redis_throttle import RedisThrottle
from django.conf import settings

_logger = logging.getLogger("davinci_crawling.testing")

CHROME_OPTIONS = {"chromium_bin_file": settings.CHROMIUM_BIN_FILE}


class TestRedisThrottle(CaravaggioBaseTest):
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
                self.assertTrue(2 <= times_throttled <= 3)
                quantity = 0
            else:
                self.assertEqual(0, times_throttled)
                quantity += 1

    def test_thread_throttle(self):
        def do_thread(results):
            throttle = RedisThrottle("test", seconds=10, rate=10, max_tokens=10)

            times_throttled = 0
            for x in range(10):
                _times_throttled = throttle.wait_for_token("test")
                times_throttled += _times_throttled

            results.append(times_throttled)

        results = []
        t1 = threading.Thread(target=do_thread, args=(results,))
        t2 = threading.Thread(target=do_thread, args=(results,))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        self.assertTrue(results)
        for result in results:
            self.assertTrue(result > 0)
