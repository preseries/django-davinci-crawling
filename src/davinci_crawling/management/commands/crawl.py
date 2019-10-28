# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
"""
This file has all the methods that are responsible for get the crawl params and
actually craw the data.
"""
import json
import sys
import logging
import time
import traceback
from datetime import datetime
from threading import Thread

from davinci_crawling.management.commands.utils.utils import \
    update_task_status
from davinci_crawling.management.commands.utils.multiprocessing_producer import \
    MultiprocessingProducer
from django.conf import settings
from davinci_crawling.task.models import Task, STATUS_CREATED, STATUS_FAULTY, STATUS_QUEUED
from davinci_crawling.management.commands.utils.consumer import CrawlConsumer
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand, CommandError, \
    handle_default_options
from django.core.management.base import SystemCheckError, CommandParser, \
    DjangoHelpFormatter
from django.db import connections

_logger = logging.getLogger("davinci_crawling.commands")


def _pool_tasks(interval, times_to_run):
    """
    A while that runs forever and check for new tasks on the cassandra DB,
    every new Task on DB has a created state, so this method looks for all the
    tasks that have this status.
    Args:
        interval: the interval that we should pool cassandra, on every pool;
        times_to_run: used on tests to determine that the threads will not run
        forever. [ONLY FOR TESTING]
    """
    times_run = 0
    producer = MultiprocessingProducer()
    while not times_to_run or times_run < times_to_run:
        _logger.debug("Calling pool tasks")
        all_tasks = Task.objects.filter(status=STATUS_CREATED).all()
        for task in all_tasks:
            try:
                crawler_name = task.kind
                options = json.loads(task.options)
                options = options.copy()
                options["crawler"] = crawler_name
                options["task_id"] = task.task_id

                options.update(settings.DAVINCI_CONF.get("default", {}))
                options.update(settings.DAVINCI_CONF.get(crawler_name, {}))

                # fixed options
                options["current_execution_date"] = datetime.utcnow()

                params = json.loads(task.params)

                producer.add_crawl_params(params, options)
                update_task_status(task, STATUS_QUEUED)
            except Exception as e:
                update_task_status(task, STATUS_FAULTY)
                _logger.error("Error while adding params to queue", e)
        time.sleep(interval)
        if times_to_run:
            times_run += 1


def start_tasks_pool(workers_num, interval, times_to_run=None):
    """
    Starts tasks pool.
    Args:
        workers_num: The quantity of workers to start.
        interval: Interval to wait between pool the tasks.
        times_to_run: used on tests to determine that the threads will not run
        forever.
    """
    crawl_consumer = CrawlConsumer(workers_num, times_to_run)
    _logger.info("Starting a consumer of %d processes" % workers_num)
    crawl_consumer.start()
    task_thread = Thread(target=_pool_tasks, args=(interval, times_to_run))

    try:
        _logger.info("Starting crawling params")
        task_thread.start()
    except TimeoutError:
        _logger.error("Timeout error")
    finally:
        task_thread.join()
        crawl_consumer.close()


class Command(BaseCommand):
    help = 'Start a tasks pool that looks for tasks on the DB'

    def __init__(self):
        super().__init__()
        self._parser = CommandParser(
            description="Task Pool settings",
            formatter_class=DjangoHelpFormatter,
            missing_args_message=getattr(self, 'missing_args_message', None),
            called_from_command_line=getattr(
                self, '_called_from_command_line', None),
        )

        self._parser.add_argument(
            '--workers-num',
            required=False,
            action='store',
            dest='workers_num',
            default=10,
            type=int,
            help="The number of workers (threads) to launch in parallel")
        self._parser.add_argument(
            '--interval',
            required=False,
            action='store',
            dest='interval',
            default=5,
            type=int,
            help="Interval to wait between pool the tasks")
        self._parser.add_argument(
            '--settings',
            help=(
                'The Python path to a settings module, e.g. '
                '"myproject.settings.main". If this isn\'t provided, the '
                'DJANGO_SETTINGS_MODULE environment variable will be used.'
            ),
        )
        self._parser.add_argument(
            '--pythonpath',
            help='A directory to add to the Python path, e.g. '
                 '"/home/djangoprojects/myproject".',
        )
        self._parser.add_argument(
            '--no-color',
            action='store_true', dest='no_color',
            help="Don't colorize the command output.",
        )
        self._parser.add_argument(
            '--force-color', action='store_true',
            help='Force colorization of the command output.',
        )

    def run_from_argv(self, argv):
        _logger.info("Starting task pool")

        parser = self._parser
        options, known_args = parser.parse_known_args(argv[2:])

        cmd_options = vars(options)
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
        workers_num = options.get("workers_num")
        interval = options.get("interval")

        start_tasks_pool(workers_num, interval)
