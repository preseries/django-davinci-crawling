# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import abc
from abc import ABCMeta


class Producer(metaclass=ABCMeta):
    """
    An abstract class that defines the necessary methods to be a producer.

    All the algorithms that we need to add to the crawl params flow we should
    use this abstraction.
    """

    @abc.abstractmethod
    def add_crawl_params(self, param, options):
        raise NotImplementedError()
