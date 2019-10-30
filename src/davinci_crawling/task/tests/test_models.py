# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import json
import logging
import time

from caravaggio_rest_api.haystack.backends.utils import \
    CaravaggioSearchPaginator
from caravaggio_rest_api.utils import delete_all_records
from davinci_crawling.task.models import Task, STATUS_CREATED, ON_DEMAND_TASK

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

        options = {
            "workers_num": "4",
            "chromium_bin_file":
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "cached_dir": "gs://my_crawler_cache",
            "local_dir": "fs:///data/crawler_one/local",
            "included_companies": '["4170", "14249"]',
            "from_date": "2018-01-01T00:00:00.000000Z",
            "crawling_initials": '["V", "P"]'
        }

        params = {
            "ccvm": 4170,
            "doc_type": "DFP",
            "fiscal_date": "2018-12-31",
            "version": "2.0"
        }

        task_data = {
            "user": "user1",
            "status": STATUS_CREATED,
            "kind": "bovespa",
            "options": options,
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
            task_params = json.loads(task.params)
            assert isinstance(task_params, dict)
            assert len(task_params) == len(params)
            assert task_params == params

            task_options = json.loads(task.options)
            assert isinstance(task_options, dict)
            assert len(task_options) == len(options)
            assert task_options == options
