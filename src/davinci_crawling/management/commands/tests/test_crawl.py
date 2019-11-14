# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.example.bovespa.crawlers import BovespaCrawler
from davinci_crawling.example.bovespa.models import BovespaCompanyFile, \
    FILE_STATUS_PROCESSED
from davinci_crawling.management.commands.crawl import start_crawl
from davinci_crawling.management.producer import Producer
from django.conf import settings


from davinci_crawling.task.models import ON_DEMAND_TASK, Task,\
    STATUS_FINISHED, STATUS_CREATED, STATUS_IN_PROGRESS, STATUS_QUEUED,\
    STATUS_FAULTY, STATUS_UNKNOWN

# Default crawler params, you may change any default value if you want
# All the things written with None value should be overwritten inside the test
CRAWLER_OPTIONS = {
    "chromium_bin_file": settings.CHROMIUM_BIN_FILE,
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

test_queue = []


class TestProducer(Producer):
    """
    Custom producer for tests that simple add params to a list.
    """

    def add_crawl_params(self, param, options):
        _logger.debug("Adding param %s to queue", param)
        test_queue.append([param, options])


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

    def create_task(self, kind, include_companies=None,
                    from_date=None, to_date=None, crawling_initials=None,
                    status=STATUS_CREATED, should_fail=False):
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

        bovespa_crawler = BovespaCrawler()
        bovespa_crawler.crawl_params(TestProducer(), **crawler_options)

        for param in test_queue:
            task = {
                "options": param[1],
                "params": param[0],
                "kind": kind,
                "user": "someuser",
                "type": ON_DEMAND_TASK,
                "status": status
            }

            if should_fail:
                task["kind"] = "something_else"
            Task.create(**task)

    def test_pool(self):
        """
        Test the pooling DB method, this test will create some tasks on the DB
        and then will start the crawl "command" when everything is done we
        validate if we have all the files on DB and if the tasks ran in
        parallel.
        """
        self.create_task("bovespa", ["4170"], "2011-01-01T00:00:00.000000Z",
                         "2011-12-31T00:00:00.000000Z", ["V"])

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
        self.assertEqual(len(tasks), files_count)

    def test_wrong_tasks(self):
        """
        Test the pooling DB method, when the task has a status different than
        CREATED, the pool should not start to execute tasks with these
        statuses.
        """
        all_status = [STATUS_QUEUED, STATUS_IN_PROGRESS, STATUS_FINISHED,
                      STATUS_FAULTY, STATUS_UNKNOWN]
        for status in all_status:
            self.create_task("bovespa", ["4170"],
                             "2011-01-01T00:00:00.000000Z",
                             "2011-12-31T00:00:00.000000Z", ["V"],
                             status=status)
            start_crawl(workers_num=WORKERS_NUM, interval=1, times_to_run=5)

            files = BovespaCompanyFile.objects.filter(
                status=FILE_STATUS_PROCESSED).all()
            # As this will not be processed we will not have any processed file
            files_count = len(files)
            self.assertEqual(files_count, 0)

    def test_failing_tasks(self):
        """
        Test the pooling DB method, when the task has a status different than
        CREATED, the pool should not start to execute tasks with these
        statuses.
        """
        self.create_task("bovespa", ["4170"], "2011-01-01T00:00:00.000000Z",
                         "2011-12-31T00:00:00.000000Z", ["V"],
                         should_fail=True)

        start_crawl(workers_num=WORKERS_NUM, interval=1, times_to_run=20)

        files = BovespaCompanyFile.objects.filter(
            status=FILE_STATUS_PROCESSED).all()
        # With this options we always have 5 files, unless any file got deleted
        # this assert should be 5
        files_count = len(files)
        self.assertEqual(files_count, 0)

        tasks = Task.objects.filter(status=STATUS_FINISHED).all()
        self.assertEqual(len(tasks), 0)

        tasks = Task.objects.filter(status=STATUS_FAULTY).all()
        self.assertEqual(len(tasks), 5)
