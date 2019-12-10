# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import asyncio
import atexit
import logging
import multiprocessing
import signal
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

from davinci_crawling.proxy.proxy import ProxyManager
from django.conf import settings

PROXY_MANAGER = ProxyManager()

_logger = logging.getLogger("davinci_crawling")


def _check_time(host, port, proxy_order, times_run=5):
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
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, int(port)))
        except Exception:
            # if returns an error we will disconsider this proxy with the
            # return -1
            return -1

        results.append(time.time() * 1000 - start_time)

    return mean(results), proxy_order


def assure_proxy_quality(pool):
    proxies = PROXY_MANAGER.get_available_proxies()
    proxies_to_check = []

    if proxies is None:
        return

    proxies_by_speed = []

    for i, proxy in enumerate(proxies):
        proxy_address = proxy["http"]
        proxy_address = proxy_address.replace("http://", "")

        host = proxy_address.split("@")[-1]
        host = host.split(":")[0]
        port = proxy_address.split(":")[-1]

        proxies_to_check.append((host, port, i))

    results = pool.starmap(_check_time, proxies_to_check)
    results = sorted(results, key=lambda x: x[0], reverse=False)

    for took_time, proxy_position in results:
        if took_time > 0:
            _proxy = proxies[proxy_position]
            if _proxy:
                proxies_by_speed.append(_proxy)

    PROXY_MANAGER.set_to_use_proxies(proxies_by_speed)


def periodic_checker():
    sleep_time = settings.DAVINCI_CONF["architecture-params"]["proxy"][
        "proxies-availability-checker"]["elapse-time-between-checks"]
    pool = multiprocessing.Pool(4)
    while not event.isSet():
        assure_proxy_quality(pool)
        time.sleep(sleep_time)


event = threading.Event()
try:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(periodic_checker)
except asyncio.CancelledError:
    pass
