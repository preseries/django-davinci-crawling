# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.example.bovespa.crawlers import BovespaCrawler
from davinci_crawling.example.bovespa.models import BovespaCompanyFile, \
    FILE_STATUS_PROCESSED
from davinci_crawling.management.commands.crawl import crawl_command
from django.conf import settings

# Default crawler params, you may change any default value if you want
# All the things written with None value should be overwritten inside the test
CRAWLER_PARAMS = {"chromium_bin_file":
                         "/Applications/Chromium.app/Contents/MacOS/Chromium",
                         "include_companies": None,
                         "local_dir": "fs://%s/../log/local" %
                                      settings.BASE_DIR,
                         "cache_dir": "fs://%s/../log/cache" %
                                      settings.BASE_DIR,
                         "crawler": None,
                         "from_date": None,
                         "to_date": None,
                         "crawling_initials": None,
                         "workers_num": 4}


class CommandsTest(CaravaggioBaseTest):
    """
    Test the producer consumer parallelism on the crawler's implementation.

    This test guarantees that the que queue works and that the consumer is
    parallel.
    """

    @classmethod
    def setUpTestData(cls):
        pass

    def test_for_one_company(self):
        crawler_params = CRAWLER_PARAMS.copy()
        # includes only the Vale company
        crawler_params["include_companies"] = ["4170"]
        # indicates the crawler to use
        crawler_params["crawler"] = "bovespa"
        # indicates the period that we should crawl the data
        crawler_params["from_date"] = "2011-01-01T00:00:00.000000Z"
        crawler_params["to_date"] = "2011-12-31T00:00:00.000000Z"
        # includes only companies that start with "V"
        crawler_params["crawling_initials"] = ["V"]

        crawl_command(BovespaCrawler, **crawler_params)

        all_items = BovespaCompanyFile.objects.filter(
            status=FILE_STATUS_PROCESSED).count()
        # With this options we always have 5 files, unless any file got deleted
        # this assert should be 5
        assert all_items == 5

    def test_for_four_companies(self):
        crawler_params = CRAWLER_PARAMS.copy()
        # includes only the Vale company
        crawler_params["include_companies"] = ["4170", "14249",
                                               "24295", "20796"]
        # indicates the crawler to use
        crawler_params["crawler"] = "bovespa"
        # indicates the period that we should crawl the data
        crawler_params["from_date"] = "2018-01-01T00:00:00.000000Z"
        crawler_params["to_date"] = "2018-06-30T00:00:00.000000Z"
        # includes only companies that start with "V"
        crawler_params["crawling_initials"] = ["V", "P", "B"]

        crawl_command(BovespaCrawler, **crawler_params)

        all_items = BovespaCompanyFile.objects.filter(
            status=FILE_STATUS_PROCESSED).count()
        # With this options we always have 9 files, unless any file got deleted
        # this assert should be 9
        assert all_items == 9

