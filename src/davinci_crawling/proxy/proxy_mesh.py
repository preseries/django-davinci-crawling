# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging
import random

from davinci_crawling.net import get_json
from davinci_crawling.proxy.proxy import Proxy
from django.conf import settings

AUTHORIZED_PROXIES_URL = "https://proxymesh.com/api/proxies/"

PROXY_MESH_SETTINGS = settings.DAVINCI_CONF["architecture-params"]["proxy"][
    "proxy_mesh"]

PROXY_TEMPLATE = "%s:%s@%s"

_logger = logging.getLogger("davinci_crawling")


class ProxyMesh(Proxy):

    available_proxies = None

    @classmethod
    def _get_available_proxies(cls):
        """
        Proxy Mesh has a list of proxies to use, this method will acess proxy
        mesh api to get this list of ips.
        Returns:

        """
        if not cls.available_proxies:
            custom_header = {
                "authorization": PROXY_MESH_SETTINGS["authentication"]
            }
            response = get_json(PROXY_MESH_SETTINGS["authorized_proxies_url"],
                                custom_header=custom_header, use_proxy=False)
            response = response.json()
            proxies = []

            for proxy in response["proxies"]:
                _proxy = PROXY_TEMPLATE % (settings.PROXY_MESH_USER,
                                           settings.PROXY_MESH_PASSWORD,
                                           proxy)
                _proxy = {
                    'proxy': {
                        'http': 'http://' + _proxy,
                        'https': 'https://' + _proxy,
                        'no_proxy': 'localhost,127.0.0.1'   # excludes
                    }
                }
                proxies.append(_proxy)
            cls.available_proxies = proxies

        return cls.available_proxies

    def get_proxy_address(self):
        """
        Just get the list of available proxies and random select a proxy.
        """
        proxies = self._get_available_proxies()

        if not proxies:
            return None

        proxy = random.choice(proxies)
        _logger.debug("Using %s proxy", proxy["proxy"]["http"].split("@")[1])
        return proxy
