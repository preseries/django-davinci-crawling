# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.

from django.apps import AppConfig


class DaVinciCrawlerConfig(AppConfig):
    name = 'davinci_crawling.task'
    verbose_name = "Django DaVinci Crawler task"

    def ready(self):
        pass
        # Add System checks
        # from .checks import pagination_system_check  # NOQA
