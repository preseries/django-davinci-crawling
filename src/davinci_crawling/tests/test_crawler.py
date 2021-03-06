# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.example.bovespa.models import BovespaCompany
from davinci_crawling.task.models import STATUS_CREATED, ON_DEMAND_TASK, Task
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
        if hasattr(settings, "DAVINCI_CONF") and "crawler-params" in settings.DAVINCI_CONF:
            all_defaults.update(settings.DAVINCI_CONF["crawler-params"].get("default", {}))
            all_defaults.update(settings.DAVINCI_CONF["crawler-params"].get("bovespa", {}))

        for key, value in all_defaults.items():
            self.assertEquals(value, parser.get_default(key))

    @staticmethod
    def _create_bovespa_company(ccvm, company_name, situation):
        data = {"ccvm": ccvm, "company_name": company_name, "situation": situation}

        return BovespaCompany(**data)

    def test_register_differences(self):
        crawler_clazz = CrawlersRegistry().get_crawler("bovespa")

        crawler = crawler_clazz()

        task_data = {
            "user": "user1",
            "status": STATUS_CREATED,
            "kind": "bovespa",
            "params": "{}",
            "options": "{}",
            "type": ON_DEMAND_TASK,
        }
        task = Task.create(**task_data)

        bovespa_previous = self._create_bovespa_company("123", "BGDS", "CREATED")
        bovespa_current = self._create_bovespa_company("123", "OpenExchange", "CREATED")

        crawler.register_differences(
            previous_object=bovespa_previous, current_object=bovespa_current, task_id=task.task_id
        )

        task = Task.objects.filter(task_id=task.task_id).first()

        expected = sorted(["created_at", "updated_at", "company_name"])
        updated_fields = sorted(task.updated_fields)
        changed_fields = sorted(task.changed_fields)

        self.assertListEqual(expected, updated_fields)
        self.assertListEqual([], task.deleted_fields)
        self.assertListEqual([], task.inserted_fields)
        self.assertListEqual(expected, changed_fields)
        self.assertIsNotNone(task.differences_from_last_version)

    def test_register_differences_already_computed(self):
        crawler_clazz = CrawlersRegistry().get_crawler("bovespa")

        crawler = crawler_clazz()

        task_data = {
            "user": "user1",
            "status": STATUS_CREATED,
            "kind": "bovespa",
            "params": "{}",
            "options": "{}",
            "type": ON_DEMAND_TASK,
        }
        task = Task.create(**task_data)

        already_computed = {
            "all": {"updates": {"created_at": {"new_value": 1, "old_value": 0}}},
            "inserts": [],
            "updates": ["created_at"],
            "deletes": [],
        }
        crawler.register_differences(already_computed_diff=already_computed, task_id=task.task_id)

        task = Task.objects.filter(task_id=task.task_id).first()

        expected = sorted(["created_at"])
        updated_fields = sorted(task.updated_fields)
        changed_fields = sorted(task.changed_fields)

        self.assertListEqual(expected, updated_fields)
        self.assertListEqual([], task.deleted_fields)
        self.assertListEqual([], task.inserted_fields)
        self.assertListEqual(expected, changed_fields)
        self.assertIsNotNone(task.differences_from_last_version)
