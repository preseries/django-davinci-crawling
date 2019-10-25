# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.

from django.apps import AppConfig


class DaVinciCrawlerConfig(AppConfig):
    name = 'bgds_task'
    verbose_name = "Django DaVinci Crawler bgds_task"

    def ready(self):
        pass
        # Add System checks
        # from .checks import pagination_system_check  # NOQA
