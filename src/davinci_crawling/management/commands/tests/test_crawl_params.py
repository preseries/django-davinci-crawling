# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import datetime
import logging

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.example.bovespa.models import BovespaCompanyFile, \
    FILE_STATUS_PROCESSED
from davinci_crawling.management.commands.crawl import start_tasks_pool
from davinci_crawling.management.commands.crawl_params import \
    crawl_command_to_task
from django.conf import settings

# Default crawler params, you may change any default value if you want
# All the things written with None value should be overwritten inside the test
from task.models import ON_DEMAND_TASK, Task, STATUS_IN_PROGRESS

CRAWLER_PARAMS = {
    'from_date': None, 'to_date': None,
    'crawling_initials': None,
    'no_update_companies_listing': False,
    'no_update_companies_files': False,
    'force_download': False, 'include_companies': None,
    'crawler': 'bovespa'
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

    def test_pool(self):
        CRAWLER_PARAMS["crawling_initials"] = ["V"]
        CRAWLER_PARAMS["include_companies"] = ["4170"]
        CRAWLER_PARAMS["from_date"] = "2011-01-01T00:00:00.000000Z"
        CRAWLER_PARAMS["to_date"] = "2011-12-31T00:00:00.000000Z"

        crawl_command_to_task(**CRAWLER_PARAMS)
        start_tasks_pool(workers_num=WORKERS_NUM, interval=1, times_to_run=20)

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
