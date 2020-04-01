# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from caravaggio_rest_api.tests import CaravaggioBaseTest
from davinci_crawling.proxy.proxy_mesh import ProxyMesh
from django.conf import settings

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
        proxies = proxy_mesh.get_to_use_proxies()
        self.assertTrue(len(proxies) > 0)

    def test_available_proxies_with_country_restrictions(self):
        """
        Test if we can get the available proxies from the proxy mesh api,
        with country restrictions on the settings.
        """
        proxy_mesh_settings = settings.DAVINCI_CONF["architecture-params"]["proxy"]["proxy_mesh"]

        self._assert_proxies_are_from(proxy_mesh_settings, ["fr"])
        self._assert_proxies_are_from(proxy_mesh_settings, ["us"])
        self._assert_proxies_are_from(proxy_mesh_settings, ["fr", "us"])

    def _assert_proxies_are_from(self, proxy_mesh_settings, countries):
        countries_str = ",".join(countries)

        proxy_mesh_settings["only-proxies-from"] = countries_str
        ProxyMesh.to_use_proxies = None
        ProxyMesh.available_proxies = None
        proxy_mesh = ProxyMesh()
        proxies = proxy_mesh.get_to_use_proxies()
        for proxy in proxies:
            proxy_http = proxy["http"]
            proxy_http = proxy_http.split("@")[1]
            proxy_country = proxy_http[0:2]

            for country in countries:
                if country == proxy_country:
                    break
            else:
                self.fail("Returned an invalid country")

    def test_get_proxy_address(self):
        """
        Test the proxy address get.
        """
        all_proxies = ProxyMesh.get_available_proxies()

        received_proxies = set()
        for _ in range(50):
            proxy = ProxyMesh().get_proxy_address()
            received_proxies.add(proxy["http"])

        # assert that we generated at least 50% of the possible values for
        # proxy
        self.assertTrue(len(received_proxies) > len(all_proxies) * 0.5)
