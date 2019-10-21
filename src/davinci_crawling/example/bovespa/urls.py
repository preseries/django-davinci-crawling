# -*- coding: utf-8 -*-
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
from django.conf.urls import url, include

from davinci_crawling.example.bovespa.api.views import \
    BovespaCompanyViewSet, BovespaCompanySearchViewSet, \
    BovespaCompanyFileViewSet, BovespaCompanyFileSearchViewSet, \
    BovespaAccountViewSet, BovespaAccountSearchViewSet

from rest_framework import routers

# API v1 Router. Provide an easy way of automatically determining the URL conf.

api_BOVESPA = routers.DefaultRouter()

api_BOVESPA.register(r'company-file/search',
                     BovespaCompanyFileSearchViewSet,
                     base_name="bovespa-company-file-search")

api_BOVESPA.register(r'company-file',
                     BovespaCompanyFileViewSet,
                     base_name="bovespa-company-file")

api_BOVESPA.register(r'company-account/search',
                     BovespaAccountSearchViewSet,
                     base_name="bovespa-company-account-search")

api_BOVESPA.register(r'company-account',
                     BovespaAccountViewSet,
                     base_name="bovespa-company-account")

api_BOVESPA.register(r'company/search',
                     BovespaCompanySearchViewSet,
                     base_name="bovespa-company-search")

api_BOVESPA.register(r'company',
                     BovespaCompanyViewSet, base_name="bovespa-company")

urlpatterns = [
    # Company API version
    url(r'^', include(api_BOVESPA.urls), name="bovespa-api"),
]
