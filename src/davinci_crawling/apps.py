# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

from django.apps import AppConfig


class DaVinciCrawlingConfig(AppConfig):
    name = 'davinci_crawling'
    verbose_name = "Django DaVinci Crawling Framework"

    def ready(self):
        pass
        # Add System checks
        # from .checks import pagination_system_check  # NOQA
