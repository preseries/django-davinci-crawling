# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.example.bovespa.models import BovespaCompanyFile, \
    FILE_STATUS_PROCESSED
from davinci_crawling.management.commands.tasks_pool import start_tasks_pool
from django.conf import settings

# Default crawler params, you may change any default value if you want
# All the things written with None value should be overwritten inside the test
from task.models import ON_DEMAND_TASK, Task, STATUS_IN_PROGRESS

CRAWLER_PARAMS = {
    "chromium_bin_file":
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "include_companies": None,
    "local_dir": "fs://%s/log/local" %
                 settings.TESTS_TMP_DIR,
    "cache_dir": "fs://%s/log/cache" %
                 settings.TESTS_TMP_DIR,
    "crawler": None,
    "from_date": None,
    "to_date": None,
    "crawling_initials": None
}

WORKERS_NUM = 5

_logger = logging.getLogger("davinci_crawling.testing")


class TasksPoolTest(CaravaggioBaseTest):
    """
    Test the producer consumer parallelism on the crawler's implementation.

    This test guarantees that the que queue works and that the consumer is
    parallel.
    """

    all_files_count = 0

    @classmethod
    def setUpTestData(cls):
        pass

    def create_task(self, kind, include_companies=None,
                    from_date=None, to_date=None, crawling_initials=None):
        crawler_params = CRAWLER_PARAMS.copy()
        # includes only the Vale company
        crawler_params["include_companies"] = include_companies
        # indicates the crawler to use
        crawler_params["crawler"] = kind
        # indicates the period that we should crawl the data
        crawler_params["from_date"] = from_date
        crawler_params["to_date"] = to_date
        # includes only companies that start with "V"
        crawler_params["crawling_initials"] = crawling_initials

        task = {
            "params": crawler_params,
            "kind": kind,
            "user": "someuser",
            "type": ON_DEMAND_TASK
        }

        Task.create(**task)

    def test_pool(self):
        self.create_task("bovespa", ["4170"], "2011-01-01T00:00:00.000000Z",
                         "2011-12-31T00:00:00.000000Z", ["V"])

        start_tasks_pool(workers_num=5, interval=1, times_to_run=20)

        files = BovespaCompanyFile.objects.filter(
            status=FILE_STATUS_PROCESSED).all()
        # With this options we always have 5 files, unless any file got deleted
        # this assert should be 5
        files_count = len(files)
        self.assertEqual(files_count, 5)

        threads_count = len(set([x.thread_id for x in files]))
        assert threads_count == WORKERS_NUM

        tasks = Task.objects.filter(status=STATUS_IN_PROGRESS).all()
        self.assertEqual(len(tasks), 1)
