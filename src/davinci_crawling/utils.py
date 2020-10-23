# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import importlib
import inspect
import logging
import time
from functools import wraps

import django

from importlib import import_module

from django.utils import timezone
from django_cassandra_engine.connection import CassandraConnection

from caravaggio_rest_api.utils import get_database

_logger = logging.getLogger("davinci_crawling")


class CrawlersRegistry(object):

    import_template = "{app_name}.crawlers"

    __crawlers = {}

    __available_crawlers = {}

    @classmethod
    def __get_installed_apps(cls):
        """
        Return list of all installed apps
        """
        if django.VERSION >= (1, 7):
            from django.apps import apps

            return [a.name for a in apps.get_app_configs()]
        else:
            from django.db import models

            return models.get_apps()

    @classmethod
    def _get_crawler_class(cls, crawler_name):
        all_crawlers = cls.get_all_crawlers()
        if crawler_name not in cls.__crawlers:
            from .crawler import Crawler

            module_name = all_crawlers[crawler_name]
            crawlers_module = import_module(module_name)

            for name, obj in inspect.getmembers(crawlers_module, inspect.isclass):
                crawler_types = Crawler
                if inspect.isclass(obj) and issubclass(obj, crawler_types) and not inspect.isabstract(obj):
                    cls.__crawlers[crawler_name] = obj
                    break

        return cls.__crawlers[crawler_name]

    @classmethod
    def _get_available_crawlers(cls):
        apps = cls.__get_installed_apps()

        for app in apps:
            try:
                module_name = cls.import_template.format(app_name=app)
                crawler_module_exists = importlib.util.find_spec(module_name)

                if not crawler_module_exists:
                    continue

                crawlers_module = import_module(app)
                crawler_name = getattr(crawlers_module, "CRAWLER_NAME")

                if crawler_name:
                    cls.__available_crawlers[crawler_name] = module_name
            except ModuleNotFoundError:
                pass

    def get_crawler(self, name):
        crawler_clazz = self._get_crawler_class(name)
        if not crawler_clazz:
            raise LookupError("Unable to find the crawler with name {}".format(name))

        return crawler_clazz

    @classmethod
    def get_all_crawlers(cls):
        if not cls.__available_crawlers:
            cls._get_available_crawlers()

        return cls.__available_crawlers


def setup_cassandra_object_mapper(alias="cassandra"):
    try:
        from dse.cqlengine import connection
    except ImportError:
        from cassandra.cqlengine import connection

    db = get_database(None, alias=alias)
    CassandraConnection("default", **db.settings_dict).register()


def get_class_from_name(class_name):
    module_name = ".".join(class_name.split(".")[:-1])
    clazz_name = class_name.split(".")[-1]

    module = importlib.import_module(module_name)
    return getattr(module, clazz_name)


class TimeIt:
    def __init__(self, prefix="", list_parameter_name=None, log_time=True):
        if not list_parameter_name:
            self.list_parameter_name = "execution_times"
        else:
            self.list_parameter_name = list_parameter_name
        self.log_time = log_time
        self.prefix = prefix

    def get_execution_times(self, fn, args, kwargs):
        execution_times_list = None
        if self.list_parameter_name:
            execution_times_list = kwargs.get(self.list_parameter_name)

            if not execution_times_list:
                arguments = inspect.getfullargspec(fn).args
                if self.list_parameter_name in arguments:
                    argument_position = arguments.index(self.list_parameter_name)
                    if argument_position < len(args):
                        execution_times_list = args[argument_position]
        return execution_times_list

    @staticmethod
    def write_times_to_more_info(davinci_task_id, executions_times):
        from davinci_crawling.task.models import TaskMoreInfo, Task

        davinci_task = Task.objects.get(task_id=davinci_task_id)

        if not davinci_task.more_info:
            more_info = []
        else:
            more_info = davinci_task.more_info

        for execution_time in executions_times:
            more_info.append(TaskMoreInfo(**execution_time))

        # TODO: find a better way to deal with this frozen update on collection
        davinci_task.more_info = None
        davinci_task.save()
        davinci_task.more_info = more_info
        davinci_task.save()

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            execution_times_list = self.get_execution_times(fn, args, kwargs)

            start_time = time.time()
            # Call the actual method
            result = fn(*args, **kwargs)
            end_time = time.time()

            duration_time_milliseconds = int((end_time - start_time) * 1000)
            method_name = self.prefix + "_" + fn.__name__

            if self.log_time:
                _logger.debug("Method %s executed for %d milliseconds" % (method_name, duration_time_milliseconds))

            if execution_times_list is not None:
                execution_times_list.append(
                    {"source": method_name, "created_at": timezone.now(), "details": str(duration_time_milliseconds)}
                )

            return result

        return wrapper
