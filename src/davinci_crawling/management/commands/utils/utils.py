# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
"""
Some utils used by the davinci_crawling commands.
"""
from davinci_crawling.utils import CrawlersRegistry
from davinci_crawling.task.models import Task, TaskMoreInfo
from django.utils import timezone

cached_crawlers = {}


def append_more_info(task, source, more_info):
    if not task.more_info:
        return [TaskMoreInfo(**{"source": source, "created_at": timezone.now(),
                                "details": more_info})]

    task.more_info.append(TaskMoreInfo(**{"source": source,
                                          "created_at": timezone.now(),
                                          "details": more_info}))
    return task.more_info


def update_task_status(task, status, source=None, more_info=None):
    """
    Get a task td to change the status on the DB.
    Args:
        task: the task that should be updated, can be either a django model or
        a UUID for the task.
        status: the status that we want to put the task on.
        source: from where the update task status was called.
        more_info: more info about the status that is being reported, generally
        use on the FAULTY state.
    """
    if not isinstance(task, Task):
        task = Task.objects.get(task_id=task)

    if not task:
        raise Exception("Not found task")

    data = {"status": status}
    if more_info:
        data["more_info"] = append_more_info(task, source, more_info)

    task.update(**data)

    return task


def get_crawler_by_name(crawler_name):
    """
    Get the crawler object using the name, this will use a cache to optimize
    the lookup for the crawler.
    Args:
        crawler_name: the name of the crawler that we need the object.

    Returns:

    """
    crawler = cached_crawlers.get(crawler_name)
    if not crawler:
        crawler_clazz = CrawlersRegistry().get_crawler(crawler_name)

        crawler = crawler_clazz()
        cached_crawlers[crawler_name] = crawler

    return crawler
