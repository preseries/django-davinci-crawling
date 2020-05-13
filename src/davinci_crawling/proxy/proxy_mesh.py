# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import copy
import logging
import random
import time

import requests
from davinci_crawling.net import get_json
from davinci_crawling.proxy.proxy import Proxy
from django.conf import settings

AUTHORIZED_PROXIES_URL = "https://proxymesh.com/api/proxies/"

PROXY_TEMPLATE = "%s:%s@%s"

_logger = logging.getLogger("davinci_crawling")


def get_machine_ip():
    response = get_json("https://api.ipify.org?format=json", use_proxy=False)
    return response


def get_proxy_mesh_settings():
    if (
        hasattr(settings, "DAVINCI_CONF")
        and "proxy" in settings.DAVINCI_CONF["architecture-params"]
        and "proxy_mesh" in settings.DAVINCI_CONF["architecture-params"]["proxy"]
    ):
        return settings.DAVINCI_CONF["architecture-params"]["proxy"]["proxy_mesh"]
    else:
        return None


PROXY_MESH_SETTINGS = get_proxy_mesh_settings()


class ProxyMesh(Proxy):

    available_proxies = None
    to_use_proxies = None

    def get_to_use_proxies(self):
        if not self.to_use_proxies:
            self.to_use_proxies = self.get_available_proxies()

        return self.to_use_proxies

    def set_to_use_proxies(self, proxies):
        self.to_use_proxies = proxies

    @classmethod
    def _authenticate_proxy_mesh(cls):
        result_machine_ip = get_machine_ip()

        tries = 10
        while result_machine_ip.status_code >= 400 and tries > 0:
            time.sleep(1)
            result_machine_ip = get_machine_ip()
            tries -= 1

        ip = result_machine_ip.json()["ip"]

        custom_header = {"authorization": PROXY_MESH_SETTINGS["authentication"]}
        try:
            response = requests.post(url=PROXY_MESH_SETTINGS["add_ip_url"], data={"ip": ip}, headers=custom_header,)
        except Exception as e:
            _logger.error(e)
            response = None
        tries = 10
        while (not response or response.status_code >= 400) and tries > 0:
            if response and "IP address is already authorized" in response.text:
                break

            time.sleep(1)
            try:
                response = requests.post(url=PROXY_MESH_SETTINGS["add_ip_url"], data={"ip": ip}, headers=custom_header,)
            except Exception as e:
                _logger.error(e)
                response = None
            tries -= 1

        _logger.debug("Successfully authenticate to ProxyMesh")

    @classmethod
    def get_country_from_proxy_address(cls, proxy_address):
        """
        Extract the country from the proxy_address, that are the first two
        letters on the domain before the first dot.
        Args:
            proxy_address: the proxy_address to be extract.
        Returns:
            The country from the proxy_address.
        """
        if proxy_address[0:4] == "open":
            # open is a set of proxies that have no country associated with
            return None

        return proxy_address[0:2]

    @classmethod
    def get_available_proxies(cls):
        """
        Proxy Mesh has a list of proxies to use, this method will acess proxy
        mesh api to get this list of ips.
        Returns: The list of available proxies.

        """
        if not cls.available_proxies and PROXY_MESH_SETTINGS:
            cls._authenticate_proxy_mesh()

            custom_header = {"authorization": PROXY_MESH_SETTINGS["authentication"]}
            try:
                response = get_json(
                    PROXY_MESH_SETTINGS["authorized_proxies_url"], custom_header=custom_header, use_proxy=False
                )
            except Exception as e:
                _logger.error(e)
                response = None

            tries = 10
            while (not response or response.status_code >= 400) and tries > 0:
                time.sleep(1)
                try:
                    response = get_json(
                        PROXY_MESH_SETTINGS["authorized_proxies_url"], custom_header=custom_header, use_proxy=False
                    )
                except Exception as e:
                    _logger.error(e)
                    response = None
                tries -= 1

            if not response or response.status_code >= 400:
                return []

            response = response.json()
            proxies = []

            only_proxies_from = PROXY_MESH_SETTINGS.get("only-proxies-from")
            only_proxies_from = only_proxies_from.split(",") if only_proxies_from else None
            for proxy in response["proxies"]:
                if only_proxies_from:
                    country = cls.get_country_from_proxy_address(proxy)
                    if not country:
                        continue

                    if country not in only_proxies_from:
                        continue

                _proxy = {
                    "http": "http://" + proxy,
                    "https": "https://" + proxy,
                    "no_proxy": "localhost,127.0.0.1",  # excludes
                }
                proxies.append(_proxy)
            cls.available_proxies = proxies

        return cls.available_proxies

    def get_proxy_address(self):
        """
        Just get the list of available proxies and random select a proxy.
        """
        proxies = self.get_to_use_proxies()

        if not proxies:
            return None

        quality_proxy_quantities = max(6, int(len(proxies) * 0.5))
        quality_proxy_quantities = min(quality_proxy_quantities, len(proxies))

        proxy = random.choice(proxies[0:quality_proxy_quantities])
        _logger.debug("Using %s proxy", proxy["http"])
        return copy.deepcopy(proxy)
