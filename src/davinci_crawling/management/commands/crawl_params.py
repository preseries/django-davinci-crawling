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
from task.models import Task, BATCH_TASK

_logger = logging.getLogger("davinci_crawling.commands")


crawler_clazz = None
crawler = None


def crawl_command_to_task(**options):
    """
    Get the issued crawl command and transform it to a Task on the Cassandra DB
    Args:
        options: the options that the command received.
    """
    data = {
        # TODO change this to a correct user
        "user": "batchuser",
        "kind": options.pop("crawler"),
        "params": options,
        "type": BATCH_TASK
    }
    Task.create(**data)


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
        crawl_command_to_task(**options)
