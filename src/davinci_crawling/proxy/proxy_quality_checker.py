# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import asyncio
import multiprocessing

import logging
import requests
import threading
import time
from davinci_crawling.proxy.proxy import ProxyManager
from django.conf import settings
from statistics import mean

PROXY_MANAGER = ProxyManager()

_logger = logging.getLogger("davinci_crawling")

URL_TO_TEST = "https://www.google.com"


def _check_time(proxy_address, proxy_order, times_run=3):
    """
    Check connection time for a host and port
    Args:
        host: the host to check
        port: the port to check
        proxy_order: the proxy order on the original list
        times_run: how many times to run the test (default is 5)

    Returns:
        the average time of all calls defined by times_run argument
    """
    def get_url(url, _proxy_address, timeout=10):
        requests.get(
            url=url,
            timeout=(timeout, timeout), verify=False, proxies=_proxy_address)

    results = []
    for _ in range(times_run):
        start_time = time.time() * 1000
        try:
            get_url(URL_TO_TEST, proxy_address)
        except Exception:
            # if returns an error we will disconsider this proxy with the
            # return -1
            return -1, -1

        results.append(time.time() * 1000 - start_time)

    return mean(results), proxy_order


def assure_proxy_quality(pool):
    proxies = PROXY_MANAGER.get_available_proxies()
    proxies_to_check = []

    if proxies is None:
        return

    proxies_by_speed = []

    for i, proxy in enumerate(proxies):
        proxies_to_check.append((proxy, i))

    results = pool.starmap(_check_time, proxies_to_check)
    results = sorted(results, key=lambda x: x[0], reverse=False)

    for took_time, proxy_position in results:
        if took_time > 0:
            _proxy = proxies[proxy_position]
            if _proxy:
                proxies_by_speed.append(_proxy)

    PROXY_MANAGER.set_to_use_proxies(proxies_by_speed)


def periodic_checker():
    if hasattr(settings, 'DAVINCI_CONF') and \
            "proxy" in settings.DAVINCI_CONF["architecture-params"] \
            and "proxies-availability-checker" in \
            settings.DAVINCI_CONF["architecture-params"][
                "proxy"]:
        sleep_time = settings.DAVINCI_CONF["architecture-params"]["proxy"][
            "proxies-availability-checker"].get("elapse-time-between-checks",
                                                60)
        pool = multiprocessing.Pool(4)
        while True:
            assure_proxy_quality(pool)
            time.sleep(sleep_time)


try:
    d = threading.Thread(name='periodic_checker', target=periodic_checker)
    d.setDaemon(True)
    d.start()
except asyncio.CancelledError:
    pass
