# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

import sys
import logging
import itertools
from multiprocessing.pool import Pool

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


def crawl(crawler_param, options):
    # We need to setup the Cassandra Object Mapper to work on multiprocessing
    # If we do not do that, the processes will be blocked when interacting
    # with the object mapper module
    setup_cassandra_object_mapper()

    _logger.debug("Calling crawl method: {0}".
                  format(getattr(crawler, "crawl")))

    return crawler.crawl(crawler_param, options)


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
        global crawler_clazz, crawler

        workers_num = options.get("workers_num", 1)

        results = []
        pool = Pool(processes=workers_num)

        try:
            crawler_params = crawler.crawl_params(**options)

            _logger.info("Crawler params ({0}): {1}".
                         format(len(crawler_params), crawler_params))

            func_params = []
            for crawler_param in crawler_params:
                func_params.append([crawler_param, options])

            _logger.info(
                "Starting a Pool of %d processes" % workers_num)

            #crawl(*func_params[0])
            call_results = pool.starmap(crawl, func_params)

            # Merge all the responses into one only list
            results += list(
                itertools.chain.from_iterable(call_results))

            _logger.info("Crawler results ({0}): {1}".
                         format(len(crawler_params), crawler_params))

        except TimeoutError:
            _logger.error("Timeout error")
        finally:
            pool.close()
            pool.join()
            pool.terminate()
