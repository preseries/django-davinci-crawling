# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

import inspect
import django

from importlib import import_module
from django_cassandra_engine.connection import CassandraConnection

from caravaggio_rest_api.utils import get_database
from haystack.backends import EmptyResults


class CrawlersRegistry(object):

    import_template = '{app_name}.crawlers'

    __crawlers = {}

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
    def _discover_crawlers(cls):
        apps = cls.__get_installed_apps()

        for app in apps:
            try:
                from .crawler import Crawler

                crawlers_module = import_module(
                    cls.import_template.format(app_name=app))

                for name, obj in inspect.getmembers(
                        crawlers_module, inspect.isclass):
                    crawler_types = (Crawler)
                    if inspect.isclass(obj) and \
                            issubclass(obj, crawler_types) and \
                            not inspect.isabstract(obj):
                        crawler_name = getattr(obj, "__crawler_name__")
                        cls.__crawlers[crawler_name] = obj
            except ModuleNotFoundError:
                pass

    def get_crawler(self, name):
        if not self.__crawlers:
            self._discover_crawlers()

        crawler_clazz = self.__crawlers.get(name, None)
        if not crawler_clazz:
            raise LookupError(
                "Unable to find the crawler with name {}".format(name))

        return crawler_clazz


def setup_cassandra_object_mapper(alias="cassandra"):
    try:
        from dse.cqlengine import connection
    except ImportError:
        from cassandra.cqlengine import connection

    db = get_database(None, alias=alias)
    CassandraConnection("default", **db.settings_dict).register()
