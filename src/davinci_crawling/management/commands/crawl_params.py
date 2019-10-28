# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
"""
This file has the logic of the crawl_params command, this command will discover
the params needed by the crawler and then create a task on the Cassandra DB.
"""
import sys
import logging

from davinci_crawling.management.producer import Producer
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand, CommandError, \
    handle_default_options
from django.core.management.base import SystemCheckError
from django.db import connections

from davinci_crawling.utils import \
    CrawlersRegistry
from davinci_crawling.task.models import Task, BATCH_TASK

_logger = logging.getLogger("davinci_crawling.commands")


crawler_clazz = None
crawler = None

generated_params = []


class CrawlParamsProducer(Producer):
    """
    Uses a local list to add the crawl_params, this is used to simplify the
    logic for generating crawwl params.
    """

    def add_crawl_params(self, param, options):
        _logger.debug("Adding param %s to queue", param)
        generated_params.append([param, options])


def crawl_command_to_task(**options):
    """
    Get the issued crawl command and transformss it to a Task on the DB.
    Args:
        options: the options that the command received.
    """
    crawler_name = options.get("crawler")
    _crawler_clazz = CrawlersRegistry().get_crawler(crawler_name)

    _crawler = _crawler_clazz()

    _crawler.crawl_params(CrawlParamsProducer(), **options)

    for param_options in generated_params:
        data = {
            "user": "batchuser",
            "kind": crawler_name,
            "params": param_options[0],
            "options": param_options[1],
            "type": BATCH_TASK
        }
        Task.create(**data)


class Command(BaseCommand):
    help = 'Mount the crawl params for the crawler and add them to the DB'

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
        crawl_command_to_task(**options)
