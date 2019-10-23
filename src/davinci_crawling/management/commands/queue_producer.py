# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging

from davinci_crawling.management.commands.consumer import multiprocess_queue
from davinci_crawling.management.producer import \
    CrawlParamsProducer

_logger = logging.getLogger("davinci_crawling.queue")


class CrawlParamsQueueProducer(CrawlParamsProducer):
    """
    Uses a multiprocessing queue to add params.
    """

    def add_crawl_params(self, param, options):
        _logger.debug("Adding param %s to queue", param)
        multiprocess_queue.put([param, options])
