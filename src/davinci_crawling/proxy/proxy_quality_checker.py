# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import asyncio
import os
import time
from statistics import mean

configuration = os.getenv('ENVIRONMENT', 'development').title()
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "davinci_crawling.settings")
os.environ.setdefault('DJANGO_CONFIGURATION', configuration)

import configurations   # NOQA
configurations.setup()

from davinci_crawling.proxy.proxy import ProxyManager   # NOQA

PROXY_MANAGER = ProxyManager()


async def check_time(host, port, proxy_order, times_run=5):
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
    results = []
    for _ in range(times_run):
        start_time = time.time() * 1000
        try:
            await asyncio.wait_for(
                asyncio.open_connection(host=host, port=port), timeout=10
            )
        except Exception:
            # if returns an error we will disconsider this proxy with the
            # return -1
            return -1

        results.append(time.time() * 1000 - start_time)

    return mean(results), proxy_order


def assure_proxy_quality():
    proxies = PROXY_MANAGER.get_available_proxies()
    proxies_to_check = []

    proxies_by_speed = []

    for i, proxy in enumerate(proxies):
        proxy_address = proxy["proxy"]["http"]
        proxy_address = proxy_address.replace("http://", "")

        host = proxy_address.split("@")[-1]
        host = host.split(":")[0]
        port = proxy_address.split(":")[-1]

        proxies_to_check.append((host, port, i))

    results = asyncio.get_event_loop().run_until_complete(asyncio.gather(
        *[check_time(host, port, i) for host, port, i in proxies_to_check]))

    results = sorted(results, key=lambda x: x[0], reverse=False)

    for took_time, proxy_position in results:
        if took_time > 0:
            proxies_by_speed.append(proxies[proxy_position])

    PROXY_MANAGER.set_to_use_proxies(proxies_by_speed)


assure_proxy_quality()
