# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.example.bovespa.models import BovespaCompanyFile, \
    FILE_STATUS_PROCESSED
from davinci_crawling.management.commands.crawl import start_crawl
from davinci_crawling.management.commands.crawl_params import \
    crawl_command_to_task
from davinci_crawling.task.models import Task, STATUS_FINISHED
from django.conf import settings


# Default crawler params, you may change any default value if you want
# All the things written with None value should be overwritten inside the test
CRAWLER_OPTIONS = {
    "chromium_bin_file":
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "include_companies": None,
    "local_dir": "fs://%s/log/local" %
                 settings.TESTS_TMP_DIR,
    "cache_dir": "fs://%s/log/cache" %
                 settings.TESTS_TMP_DIR,
    "crawler": "bovespa",
    "from_date": None,
    "to_date": None,
    "crawling_initials": None
}

WORKERS_NUM = 5

_logger = logging.getLogger("davinci_crawling.testing")


class TestCrawlParams(CaravaggioBaseTest):
    """
    Test the crawl_params command that simply create tasks om the database.
    This test also uses the crawl command to validate that the crawl operation
    works after creating the tasks using the crawl_params command.
    """

    all_files_count = 0

    @classmethod
    def setUpTestData(cls):
        pass

    def test_pool(self):
        CRAWLER_OPTIONS["crawling_initials"] = ["V"]
        CRAWLER_OPTIONS["include_companies"] = ["4170"]
        CRAWLER_OPTIONS["from_date"] = "2011-01-01T00:00:00.000000Z"
        CRAWLER_OPTIONS["to_date"] = "2011-12-31T00:00:00.000000Z"

        crawl_command_to_task(**CRAWLER_OPTIONS)
        start_crawl(workers_num=WORKERS_NUM, interval=1, times_to_run=20)

        files = BovespaCompanyFile.objects.filter(
            status=FILE_STATUS_PROCESSED).all()
        # With this options we always have 5 files, unless any file got deleted
        # this assert should be 5
        files_count = len(files)
        self.assertEqual(files_count, 5)

        threads_count = len(set([x.thread_id for x in files]))
        assert threads_count == WORKERS_NUM

        tasks = Task.objects.filter(status=STATUS_FINISHED).all()
        self.assertEqual(len(tasks), 5)
