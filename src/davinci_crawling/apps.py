# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
from davinci_crawling.proxy.proxy import ProxyManager
from davinci_crawling.throttle.throttle import Throttle
from django.apps import AppConfig


class DaVinciCrawlingConfig(AppConfig):
    name = 'davinci_crawling'
    verbose_name = "Django DaVinci Crawling Framework"

    def ready(self):
        from davinci_crawling.proxy import proxy_quality_checker
        ProxyManager.get_proxy_manager()
        Throttle.get_manager_clazz()
        # Add System checks
        # from .checks import pagination_system_check  # NOQA
