# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

"""
WSGI config for DaVinci project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from configurations.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "davinci_crawling.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "development")

application = get_wsgi_application()
