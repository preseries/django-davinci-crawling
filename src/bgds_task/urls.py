# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.

"""
bgds_task URL Configuration

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
from django.conf.urls import url, include

from rest_framework.schemas import get_schema_view

from bgds_task.api.urls import urlpatterns as bgds_task_urls

urlpatterns = [
    url(r'^api-schema/bgds_task/$',
        get_schema_view(title="Bgds_task API",
                        patterns=[url(r'^bgds_task/',
                                      include(bgds_task_urls))])),

    # Bgds_task API version
    url(r'^bgds_task/', include(bgds_task_urls)),
]
