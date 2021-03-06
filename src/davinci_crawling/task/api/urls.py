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
from caravaggio_rest_api.drf.routers import CaravaggioRouter
from django.conf import settings
from django.conf.urls import url, include

from davinci_crawling.task.api.views import TaskViewSet, TaskSearchViewSet

# API v1 Router. Provide an easy way of automatically determining the URL conf.

api_TASK = CaravaggioRouter()

if settings.DSE_SUPPORT:
    api_TASK.register(r"task/search", TaskSearchViewSet, base_name="task-search")

    api_TASK.register(r"task/search/facets", TaskSearchViewSet, base_name="task-search-facets")

api_TASK.register(r"task", TaskViewSet, base_name="task")

urlpatterns = [
    # Company API version
    url(r"^", include(api_TASK.urls), name="task-api"),
]
