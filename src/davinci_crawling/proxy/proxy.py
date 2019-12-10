# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import abc
from abc import ABCMeta

from davinci_crawling.utils import get_class_from_name
from django.conf import settings

DEFAULT_PROXY_IMPLEMENTATION = "davinci_crawling.proxy.proxy.NoProxy"


class Proxy(metaclass=ABCMeta):
    """
    The abstract class used to get new proxy addresses to be used on requests
    """
    @abc.abstractmethod
    def get_to_use_proxies(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def set_to_use_proxies(self, proxies):
        raise NotImplementedError()

    @classmethod
    def get_available_proxies(cls):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_proxy_address(self):
        raise NotImplementedError()


class NoProxy(Proxy):

    def get_to_use_proxies(self):
        return None

    def set_to_use_proxies(self, proxies):
        pass

    @classmethod
    def get_available_proxies(cls):
        return None

    def get_proxy_address(self):
        return None


class ProxyManager:
    """
    The proxy manager, you should only call this one, this code will decide
    which proxy to use based on the settings and will call the desired method
    on the desired class.
    """

    manager = None

    @classmethod
    def _get_proxy_implementation(cls):
        if not cls.manager:
            if hasattr(settings, 'DAVINCI_CONF') and \
                    "proxy" in settings.DAVINCI_CONF["architecture-params"]\
                    and "implementation" in settings.DAVINCI_CONF[
                    "architecture-params"]["proxy"]:
                proxy_implementation = settings.DAVINCI_CONF[
                    "architecture-params"]["proxy"]["implementation"]
            else:
                proxy_implementation = DEFAULT_PROXY_IMPLEMENTATION

            manager_clazz = get_class_from_name(proxy_implementation)

            cls.manager = manager_clazz()

        return cls.manager

    def get_proxy_address(self):
        proxy = self._get_proxy_implementation()

        return proxy.get_proxy_address()

    def get_available_proxies(self):
        proxy = self._get_proxy_implementation()

        return proxy.get_available_proxies()

    def get_to_use_proxies(self):
        proxy = self._get_proxy_implementation()

        return proxy.get_to_use_proxies()

    def set_to_use_proxies(self, proxies):
        proxy = self._get_proxy_implementation()

        return proxy.set_to_use_proxies(proxies)
