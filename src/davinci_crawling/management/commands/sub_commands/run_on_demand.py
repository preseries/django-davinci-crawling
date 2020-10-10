# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
"""
This file has all the methods that are responsible for start the subscription
consumer.
"""
import json
from datetime import datetime

import logging

from caravaggio_rest_api.sub_commander import CaravaggioSubCommand
from davinci_crawling.management.commands.utils.utils import get_crawler_by_name
from davinci_crawling.task.models import BATCH_TASK, create_davinci_task_batch
from davinci_kafka_processing.kafka.consumer import _add_default_options
from django.conf import settings

_logger = logging.getLogger("caravaggio_subscriptions.commands")


class Command(CaravaggioSubCommand):
    help = "Run tasks on demand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--crawler", action="store", dest="crawler", type=str, help="Name of the crawler", required=True,
        )
        parser.add_argument(
            "--params", action="store", dest="params", type=str, help="Parameters to the task",
        )

    def handle(self, *args, **options):
        _logger.info("Starting run_on_demand")
        crawler_name = options.get("crawler")
        params = json.loads(options.get("params"))
        data = {"user": "batchuser", "kind": crawler_name, "params": params, "type": BATCH_TASK}
        task = create_davinci_task_batch(data)

        crawler = get_crawler_by_name(crawler_name)
        _logger.debug("Calling crawl method: {0}".format(getattr(crawler, "crawl")))
        _logger.debug("Task id: {0}".format(task.task_id))

        options = {"current_execution_date": datetime.now()}
        options["crawler"] = crawler_name
        options["task_id"] = task.task_id

        default_settings = settings.DAVINCI_CONF["crawler-params"].get("default", {})
        crawler_settings = settings.DAVINCI_CONF["crawler-params"].get(crawler_name, {})

        _add_default_options(options, crawler_settings)
        _add_default_options(options, default_settings)

        crawler.crawl(task.task_id, params, options)
