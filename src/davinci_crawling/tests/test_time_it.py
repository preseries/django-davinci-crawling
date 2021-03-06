# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
import random

from django.utils import timezone

from davinci_crawling.task.models import Task, TaskMoreInfo

from caravaggio_rest_api.tests import CaravaggioBaseTest
import time
from davinci_crawling.utils import TimeIt


class TestTimeIt(CaravaggioBaseTest):
    """
    Test the abstract crawler class.
    """

    all_files_count = 0

    @classmethod
    def setUpTestData(cls):
        pass

    def test_time_it(self):
        @TimeIt()
        def method_to_time_default_parameter(execution_times=None):
            time.sleep(1)

        @TimeIt(prefix="some_prefix_")
        def method_to_time_prefix(execution_times=None):
            time.sleep(0.5)

        @TimeIt(list_parameter_name="changed_name")
        def method_to_time_changed_parameter(changed_name=None):
            time.sleep(0.1)

        self._validate_time_it(
            method_to_time_default_parameter, expected_duration=1000, expected_source="method_to_time_default_parameter"
        )
        self._validate_time_it(
            method_to_time_prefix, expected_duration=500, expected_source="some_prefix_method_to_time_prefix"
        )
        self._validate_time_it(
            method_to_time_changed_parameter, expected_duration=100, expected_source="method_to_time_changed_parameter"
        )

    def test_time_it_without_list(self):
        @TimeIt()
        def method_to_time_no_parameter():
            time.sleep(0.1)

        method_to_time_no_parameter()

    def test_write_to_task(self):
        @TimeIt()
        def method_to_time_default_parameter(a, b, c, d, execution_times=None):
            time.sleep(0.1)

        execution_times = []
        for x in range(10):
            method_to_time_default_parameter(0, 1, 2, 3, execution_times)

        task_data = {
            "user": "user1",
            "status": 1,
            "kind": "bovespa",
            "options": "{}",
            "params": "{}",
            "type": 2,
            "more_info": [TaskMoreInfo(source="test", created_at=timezone.now(), details="a")],
        }
        task = Task.create(**task_data)
        task = Task.objects.get(task_id=task.task_id)
        TimeIt.write_times_to_more_info(task, execution_times)

        task = Task.objects.get(task_id=task.task_id)
        # 10 execution_times + the existent more_info
        self.assertEquals(len(task.more_info), 11)

    def test_time_it_many_times(self):
        @TimeIt()
        def sleep_method(time_to_sleep, execution_times):
            time.sleep(time_to_sleep)

        execution_times = []
        sum_sleep = 0
        quantity_to_call = 10
        for _ in range(quantity_to_call):
            time_sleep = random.random()
            sum_sleep += int(time_sleep * 1000)
            sleep_method(time_sleep, execution_times)

        self.assertEquals(quantity_to_call, len(execution_times))
        total_sum = sum([x["details"] for x in execution_times])
        self.assertGreaterEqual(total_sum, sum_sleep)
        self.assertGreaterEqual(sum_sleep + quantity_to_call * 10, total_sum)

    def _validate_time_it(self, method_to_call, expected_duration, expected_source):
        execution_times = []
        method_to_call(execution_times)
        self.assertEquals(1, len(execution_times))
        self.assertGreaterEqual(execution_times[0]["details"], expected_duration)
        self.assertGreaterEqual(expected_duration + 10, execution_times[0]["details"])
        self.assertEquals(expected_source, execution_times[0]["source"])
