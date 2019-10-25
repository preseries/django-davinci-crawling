# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging
import time

from caravaggio_rest_api.haystack.backends.utils import \
    CaravaggioSearchPaginator
from caravaggio_rest_api.utils import delete_all_records
from bgds_task.models import Task, STATUS_CREATED, ON_DEMAND_TASK

from caravaggio_rest_api.tests import CaravaggioBaseTest

CONTENTTYPE_JON = "application/json"

_logger = logging.getLogger()


class ModelsTest(CaravaggioBaseTest):
    """ Test module for Task model """
    resources = []

    persisted_resources = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # We clean the test database (Task)
        delete_all_records(Task)

    def test_create_and_query(self):
        total = Task.objects.all()

        assert len(total) == 0

        params = {
            "workers_num": "4",
            "chromium_bin_file":
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "cached_dir": "gs://my_crawler_cache",
            "local_dir": "fs:///data/crawler_one/local",
            "included_companies": '["4170", "14249"]',
            "from_date": "2018-01-01T00:00:00.000000Z",
            "crawling_initials": '["V", "P"]'
        }
        task_data = {
            "user": "user1",
            "status": STATUS_CREATED,
            "kind": "bovespa",
            "params": params,
            "type": ON_DEMAND_TASK
        }
        Task.create(**task_data)
        task_data["user"] = "user2"
        Task.create(**task_data)
        task_data["user"] = "user3"
        Task.create(**task_data)
        total = Task.objects.all()

        assert len(total) == 3

        # we need a tiny sleep here
        time.sleep(1)

        # test without conditions
        paginator = CaravaggioSearchPaginator(
            query_string=str("user:user1"),
            limit=1000, max_limit=1000). \
            models(Task). \
            select("task_id*",)

        all_tasks = []
        while paginator.has_next():
            paginator.next()
            results = paginator.get_results()
            for d in results:
                all_tasks.append(d.task_id)

        all_tasks = Task.objects.filter(task_id__in=all_tasks).all()
        assert len(all_tasks) == 1
        for task in all_tasks:
            assert isinstance(task.params, dict)
            assert len(task.params) == len(params)
            assert task.params == params
