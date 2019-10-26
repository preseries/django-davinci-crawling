# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import sys
import logging
from multiprocessing.pool import ThreadPool

from davinci_crawling.management.commands.utils.consumer import CrawlConsumer
from davinci_crawling.management.commands.utils.multiprocessing_producer import \
    MultiprocessingProducer
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand, CommandError, \
    handle_default_options
from django.core.management.base import SystemCheckError
from django.db import connections

from davinci_crawling.utils import \
    CrawlersRegistry, setup_cassandra_object_mapper

_logger = logging.getLogger("davinci_crawling.commands")


crawler_clazz = None
crawler = None

def crawl_params(_crawler_clazz, **options):
    """
    Calls the crawl_params inside the crawler, this function is only used to
    facilitate the call by the Poll on the crawl command.
    Args:
        _crawler_clazz: The crawler class that should be used to generate the
         params;
        **options: The options that will be used to generate the params.
    """
    # We need to setup the Cassandra Object Mapper to work on multiprocessing
    # If we do not do that, the processes will be blocked when interacting
    # with the object mapper module
    setup_cassandra_object_mapper()

    _crawler = _crawler_clazz()

    _crawler.crawl_params(MultiprocessingProducer(), **options)


def crawl_command(_crawler_clazz, **options):
    """
    Call the crawler to both crawl_params and crawl the data.
    Args:
        _crawler_clazz: The crawler class, as we can't pickle the crawler obj
        we use the class to them create the object when necessary.
        _crawler: the crawler implementation that will be used to process
    the data.
        options: the options that the command received.
    """
    workers_num = options.get("workers_num", 1)
    _crawler = _crawler_clazz()
    crawl_consumer = CrawlConsumer(_crawler, workers_num)
    _logger.info("Starting a consumer of %d processes" % workers_num)
    crawl_consumer.start()
    crawl_params_producer = ThreadPool(processes=1)

    try:
        _logger.info("Starting crawling params")

        crawl_params_producer.apply(crawl_params, (_crawler_clazz,), options)
    except TimeoutError:
        _logger.error("Timeout error")
    finally:
        crawl_consumer.close()
        crawl_params_producer.close()
        crawl_params_producer.join()
        crawl_params_producer.terminate()


class Command(BaseCommand):
    help = 'Crawl data from source'

    def run_from_argv(self, argv):
        global crawler_clazz, crawler

        crawler_name = argv[2]
        _logger.info("Calling crawler: {}".format(crawler_name))

        crawler_clazz = CrawlersRegistry().get_crawler(crawler_name)

        crawler = crawler_clazz()

        parser = crawler.get_parser()
        options, known_args = \
            parser.parse_known_args(argv[2:])

        cmd_options = vars(options)
        cmd_options["crawler"] = crawler.__crawler_name__
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop('args', ())
        handle_default_options(options)
        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            if options.traceback or not isinstance(e, CommandError):
                raise

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(1)
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                # Ignore if connections aren't setup at this point (e.g. no
                # configured settings).
                pass

    def handle(self, *args, **options):
        global crawler_clazz

        crawl_command(crawler_clazz, **options)
