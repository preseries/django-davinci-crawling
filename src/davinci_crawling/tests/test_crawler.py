# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.utils import CrawlersRegistry
from django.conf import settings


class TestCrawl(CaravaggioBaseTest):
    """
    Test the abstract crawler class.
    """

    all_files_count = 0

    @classmethod
    def setUpTestData(cls):
        pass

    def test_crawler_parser(self):
        crawler_clazz = CrawlersRegistry().get_crawler("bovespa")

        crawler = crawler_clazz()

        parser = crawler.get_parser()

        all_defaults = {}
        if hasattr(settings, "DAVINCI_CONF") and "crawler-params" in \
                settings.DAVINCI_CONF:
            all_defaults.update(settings.DAVINCI_CONF["crawler-params"].get(
                "default", {}))
            all_defaults.update(settings.DAVINCI_CONF["crawler-params"].get(
                "bovespa", {}))

        for key, value in all_defaults.items():
            self.assertEquals(value, parser.get_default(key))
