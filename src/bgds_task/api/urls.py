# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
"""
Company URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2./topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include

from bgds_task.api.views import \
    TaskViewSet, \
    TaskSearchViewSet, \
    TaskGEOSearchViewSet

from rest_framework import routers

# API v1 Router. Provide an easy way of automatically determining the URL conf.

api_BGDS_TASK = routers.DefaultRouter()

if settings.DSE_SUPPORT:
    api_BGDS_TASK.register(r'bgds_task/search',
                           TaskSearchViewSet,
                           base_name="bgds_task-search")

    api_BGDS_TASK.register(r'bgds_task/search/facets',
                           TaskSearchViewSet,
                           base_name="bgds_task-search-facets")

    api_BGDS_TASK.register(r'bgds_task/geosearch',
                           TaskGEOSearchViewSet,
                           base_name="bgds_task-geosearch")

api_BGDS_TASK.register(r'bgds_task',
                       TaskViewSet,
                       base_name="bgds_task")

urlpatterns = [
    # Company API version
    url(r'^', include(api_BGDS_TASK.urls), name="task-api"),
]
