# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging
import queue
import time
from datetime import datetime
from threading import Thread

from davinci_crawling.management.commands.utils.utils import \
    update_task_status, get_crawler_by_name

from multiprocessing import Queue

from davinci_crawling.task.models import STATUS_IN_PROGRESS, STATUS_FAULTY,\
    STATUS_FINISHED

_logger = logging.getLogger("davinci_crawling.queue")

# stores the multiprocess queue used between crawl_params and crawl method
multiprocess_queue = Queue()


class CrawlConsumer(object):
    """
    Initiates a crawl consumer that reads from the multiprocessing queue.

    It processes the parameters in parallel using a determined quantity of
    workers.
    """
    consumers = []

    def __init__(self, qty_workers=2, times_to_run=None):
        """
        Args:
            qty_workers: The quantity of consumers that we want to start.
            times_to_run: how many time to run on the thread. [ONLY FOR
             TESTING]
        """
        self.consumers = []
        self.qty_workers = qty_workers
        self.cached_crawlers = {}
        self.times_to_run = times_to_run

    def start(self):
        """
        Start all the consumers that we need and store them on the
        consumers list.
        """
        for i in range(self.qty_workers):
            p = Thread(target=self._crawl_params)
            self.consumers.append(p)

        for consumer in self.consumers:
            consumer.start()

    def _crawl(self, crawler_name, task_id, crawler_param, options):
        """
        Calls the crawl method inside the crawler being used.
        Args:
            crawler_param: the parameter to add to the crawler.
            options: the options that will be used on the crawl method.

        Returns:
            The result of the crawler call.
        """
        crawler = get_crawler_by_name(crawler_name)
        _logger.debug("Calling crawl method: {0}".
                      format(getattr(crawler, "crawl")))
        return crawler.crawl(task_id, crawler_param, options)

    def join(self):
        """
        Close the consumers, and wait them to join.
        """
        _logger.debug("Joining consumers")
        for consumer in self.consumers:
            consumer.join()

    def _crawl_params(self):
        """
        Read the multiprocessing queue and call the crawl method to execute the
        crawling logic.

        Will run forever than we need to Ctrl+C to finish this.
        """
        times_run = 0
        while True:
            if self.times_to_run and times_run > self.times_to_run:
                return
            task_id = None
            try:
                crawl_param, options = multiprocess_queue.get(
                    block=False)
                crawler_name = options.get("crawler")
                task_id = options.get("task_id")
                update_task_status(task_id, STATUS_IN_PROGRESS)
                _logger.debug("Reading a queue value %s", crawl_param)

                if "current_execution_date" not in options:
                    options["current_execution_date"] = datetime.utcnow()

                self._crawl(crawler_name, task_id, crawl_param, options)
                update_task_status(task_id, STATUS_FINISHED)
            except queue.Empty:
                # Means that the queue is empty and we need to count many times
                # that the occurs to the close logic, we just start counting
                # when at least the queue received one
                _logger.debug("No objects found on queue, waiting for 1 "
                              "second and try again")
                time.sleep(1)
            except Exception as e:
                if task_id:
                    update_task_status(task_id, STATUS_FAULTY)

                # TODO add the error message to the db
                _logger.error("Error while crawling params from queue", e)
            times_run += 1
