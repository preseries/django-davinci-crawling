# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import time

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.crawler import Crawler
from davinci_crawling.management.commands.tests.test_crawl import CRAWLER_OPTIONS
from davinci_crawling.task.models import STATUS_CREATED, ON_DEMAND_TASK, Task, STATUS_FAULTY, STATUS_MAINTENANCE
from davinci_crawling.utils import CrawlersRegistry


class TestCrawl(CaravaggioBaseTest):
    """
    Test the producer consumer parallelism on the crawler's implementation.

    This test guarantees that the que queue works and that the consumer is
    parallel.
    """

    all_files_count = 0

    @classmethod
    def setUpTestData(cls):
        pass

    def create_task(
        self,
        kind,
        include_companies=None,
        from_date=None,
        to_date=None,
        crawling_initials=None,
        status=STATUS_CREATED,
        should_fail=False,
    ):
        crawler_options = CRAWLER_OPTIONS.copy()
        # includes only the Vale company
        crawler_options["include_companies"] = include_companies
        # indicates the crawler to use
        crawler_options["crawler"] = kind
        # indicates the period that we should crawl the data
        crawler_options["from_date"] = from_date
        crawler_options["to_date"] = to_date
        # includes only companies that start with "V"
        crawler_options["crawling_initials"] = crawling_initials

        task = {
            "kind": kind,
            "user": "someuser",
            "type": ON_DEMAND_TASK,
            "status": status,
            "params": {"a": "b"},
            "options": {"c": "d"},
        }

        return Task.create(**task)

    def test_error_task(self):
        """
        Test the error method.
        """
        task = self.create_task(
            "bovespa", ["4170"], "2011-01-01T00:00:00.000000Z", "2011-12-31T00:00:00.000000Z", ["V"], should_fail=True
        )

        task_id = task.task_id

        status_ = '{"status": 500}'
        status_2 = '{"status": 400}'
        crawler_clazz = CrawlersRegistry().get_crawler("bovespa")

        crawler = crawler_clazz()
        crawler.error(task_id, more_info=status_)
        crawler.error(task_id, more_info=status_2)

        task_error = Task.objects.get(task_id=task_id)

        self.assertEquals(STATUS_FAULTY, task_error.status)
        self.assertEquals(2, len(task_error.more_info))
        self.assertEquals(status_, task_error.more_info[0].details)
        self.assertEquals("bovespa", task_error.more_info[0].source)
        self.assertIsNotNone(task_error.more_info[0].created_at)

        self.assertEquals(status_2, task_error.more_info[1].details)
        self.assertEquals("bovespa", task_error.more_info[1].source)
        self.assertIsNotNone(task_error.more_info[1].created_at)

    def test_maintenance_task(self):
        """
        Test the maintenance_notice method.
        """
        kind = str(time.time())
        task = self.create_task(
            kind, ["4170"], "2011-01-01T00:00:00.000000Z", "2011-12-31T00:00:00.000000Z", ["V"], should_fail=True
        )

        task_id = task.task_id

        status_ = '{"status": 500}'
        crawler_clazz = CrawlersRegistry().get_crawler("bovespa")

        crawler = crawler_clazz()

        crawler.maintenance_notice(task_id, more_info=status_)

        task = Task.objects.all().filter(status=STATUS_MAINTENANCE, kind=kind)
        task = task.first()

        self.assertIsNotNone(task)
        self.assertEquals(STATUS_MAINTENANCE, task.status)
        self.assertEquals(status_, task.more_info[0].details)
        self.assertEquals("bovespa", task.more_info[0].source)
        self.assertIsNotNone(task.more_info[0].created_at)
