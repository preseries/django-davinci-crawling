# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.example.bovespa.crawlers import BovespaCrawler
from davinci_crawling.example.bovespa.models import BovespaCompanyFile, \
    FILE_STATUS_PROCESSED
from davinci_crawling.management.commands.crawl import start_crawl
from davinci_crawling.management.producer import Producer
from davinci_crawling.proxy.proxy_mesh import ProxyMesh
from django.conf import settings


from davinci_crawling.task.models import ON_DEMAND_TASK, Task,\
    STATUS_FINISHED, STATUS_CREATED, STATUS_IN_PROGRESS, STATUS_QUEUED,\
    STATUS_FAULTY, STATUS_UNKNOWN

_logger = logging.getLogger("davinci_crawling.testing")


class TestProxyMesh(CaravaggioBaseTest):
    """
    Test the proxy mesh logic, this test requires connection with internet
    because we use the proxy mesh api.
    """

    all_files_count = 0

    @classmethod
    def setUpTestData(cls):
        pass

    def test_available_proxies(self):
        """
        Test if we can get the available proxies from the proxy mesh api.
        """
        proxy_mesh = ProxyMesh()
        proxies = proxy_mesh._get_available_proxies()
        self.assertTrue(len(proxies) > 0)

    def test_get_proxy_address(self):
        """
        Test the proxy address get.
        """
        all_proxies = ProxyMesh._get_available_proxies()

        received_proxies = set()
        for _ in range(50):
            proxy = ProxyMesh().get_proxy_address()
            received_proxies.add(proxy["proxy"]["http"])

        # assert that we generated at least 50% of the possible values for
        # proxy
        self.assertTrue(len(received_proxies) > len(all_proxies) * 0.5)
