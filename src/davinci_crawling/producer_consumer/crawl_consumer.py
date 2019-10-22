# -*- coding: utf-8 -*
# Copyright (c) 2018-2019 BuildGroup Data Services Inc.
import logging
import queue
import time
from multiprocessing import Process, Value

from davinci_crawling.utils import setup_cassandra_object_mapper

from davinci_crawling.producer_consumer import multiprocess_queue

_logger = logging.getLogger("davinci_crawling.queue")


class CrawlConsumer(object):
    """
    Initiates a crawl consumer that reads from the multiprocessing queue.

    It processes the parameters in parallel using a determined quantity of
    workers.
    """
    consumers = []

    def __init__(self, crawler, qty_workers=2, empty_queue_times=10):
        """
        Args:
            crawler: the crawler implementation that should be used.
            qty_workers: The quantity of consumers that we want to start.
            empty_queue_times: The amount of times that the consumer should
            run with empty values to consider it`s over.
        """
        # Multiprocessing variable that indicates if the threads should stop,
        # this variable must be thread-safe to be used on all spawned threads.
        self.started = Value('b', True)
        # Used to store all the processes that we`re using on the
        # multiprocessing
        self.empty_queue_times = empty_queue_times
        self.consumers = []
        self.crawler = crawler
        self.qty_workers = qty_workers

    def start(self):
        """
        Start all the consumers that we need and store them on the
        self.consumers list.
        """
        for i in range(self.qty_workers):
            p = Process(target=self._crawl_params)
            self.consumers.append(p)

        for consumer in self.consumers:
            consumer.start()

    def _crawl(self, crawler_param, options):
        """
        Calls the crawl method inside the crawler being used.
        Args:
            crawler_param: the parameter to add to the crawler.
            options: the options that will be used on the crawl method.

        Returns:
            The result of the crawler call.
        """
        # We need to setup the Cassandra Object Mapper to work on
        # multiprocessing If we do not do that, the processes will be blocked
        # when interacting with the object mapper module
        setup_cassandra_object_mapper()

        _logger.debug("Calling crawl method: {0}".
                      format(getattr(self.crawler, "crawl")))
        return self.crawler.crawl(crawler_param, options)

    def close(self):
        """
        Close the consumers, and wait them to join.
        """
        _logger.debug("Stopping consumers")
        self.started.value = False
        for consumer in self.consumers:
            consumer.join()

    def _crawl_params(self):
        """
        Read the multiprocessing queue and call the crawl method to execute the
        crawling logic.

        Will run forever until the method close is called, when the close is
        called the self.started is set to False.
        """
        empty_queue_times = -1
        while True:
            if empty_queue_times >= self.empty_queue_times \
                    and not self.started.value:
                return

            try:
                crawl_param, options = multiprocess_queue.get(block=False)
                empty_queue_times = 0
                _logger.debug("Reading a queue value %s", crawl_param)
                self._crawl(crawl_param, options)
            except queue.Empty:
                # Means that the queue is empty and we need to count many times
                # that the occurs to the close logic.
                if empty_queue_times >= 0:
                    empty_queue_times += 1
                    _logger.debug("No objects found on queue, waiting for 1 "
                                  "second, already had %d empty queues" % (
                                      empty_queue_times))
                else:
                    _logger.debug("No objects found on queue, waiting for 1 "
                                  "second, not started yet")
                time.sleep(1)
