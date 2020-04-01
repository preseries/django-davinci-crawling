# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.

from django.apps import AppConfig


class DaVinciCrawlerConfig(AppConfig):
    name = "davinci_crawling.example.bovespa"
    verbose_name = "Django DaVinci Crawler Bovespa"

    def ready(self):
        from davinci_crawling.example.bovespa.api import serializers
