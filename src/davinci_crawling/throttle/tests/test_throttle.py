# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
import logging
import time

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.throttle.throttle import Throttle
from django.conf import settings

_logger = logging.getLogger("davinci_crawling.testing")

CHROME_OPTIONS = {
    "chromium_bin_file": settings.CHROMIUM_BIN_FILE
}


class TestThrottle(CaravaggioBaseTest):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_method_with_kwargs(self):
        @Throttle(crawler_name="test_kwargs", seconds=10, max_tokens=25,
                  rate=25, throttle_suffix_field="suffix")
        def throttle_method(prefix, suffix, print_name):
            print("%s %s %s" % (prefix, print_name, suffix))

        suffixes = ["from Brazil", "from USA"]
        start = time.time()
        for index in range(50):
            suffix = suffixes[index % 2]
            throttle_method("Mr.", suffix=suffix, print_name="John%d" % index)
        end = time.time()
        total = end - start

        self.assertTrue(10 < total < 20)

    def test_method_with_args(self):
        @Throttle(crawler_name="test_args", seconds=10, max_tokens=25, rate=25,
                  throttle_suffix_field="suffix")
        def throttle_method(prefix, suffix, print_name):
            print("%s %s %s" % (prefix, print_name, suffix))

        suffixes = ["from Brazil", "from USA"]
        start = time.time()
        for index in range(50):
            suffix = suffixes[index % 2]
            throttle_method("Mr.", suffix, "John%d" % index)
        end = time.time()
        total = end - start

        self.assertTrue(10 < total < 20)
