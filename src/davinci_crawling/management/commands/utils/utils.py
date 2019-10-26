# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
from davinci_crawling.utils import CrawlersRegistry
from task.models import Task

cached_crawlers = {}


def update_task_status(task, status):
    if not isinstance(task, Task):
        task = Task.objects.filter(task_id=task).first()

    task.update(**{"status": status})


def get_crawler_by_name(crawler_name):
    crawler = cached_crawlers.get(crawler_name)
    if not crawler:
        crawler_clazz = CrawlersRegistry().get_crawler(crawler_name)

        crawler = crawler_clazz()
        cached_crawlers[crawler_name] = crawler

    return crawler
