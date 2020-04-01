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
from persistqueue import SQLiteAckQueue

from davinci_crawling.management.commands.utils.utils import update_task_status
from django.conf import settings
from davinci_crawling.task.models import Task, STATUS_CREATED, STATUS_FAULTY, STATUS_QUEUED
from davinci_crawling.management.commands.utils.consumer import CrawlConsumer, QUEUE_LOCATION
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand, CommandError, handle_default_options
from django.core.management.base import SystemCheckError, CommandParser, DjangoHelpFormatter
from django.db import connections

_logger = logging.getLogger("davinci_crawling.commands")


def _add_default_options(options_obj, default_values):
    for key, value in default_values.items():
        if key not in options_obj or options_obj[key] is None:
            options_obj[key] = value


def _pool_tasks(interval, times_to_run):
    """
    A while that runs forever and check for new tasks on the cassandra DB,
    every new Task on DB has a 'created' state, so this method looks for all
    the tasks that have this status.
    Args:
        interval: the interval that we should pool cassandra, on every pool;
        times_to_run: used on tests to determine that the threads will not run
        forever. [ONLY FOR TESTING]
    """
    times_run = 0
    tasks_queue = SQLiteAckQueue(QUEUE_LOCATION)
    # this while condition will only be checked on testing, otherwise this loop
    # should run forever.
    while not times_to_run or times_run < times_to_run:
        _logger.debug("Calling pool tasks")
        all_tasks = Task.objects.filter(status=STATUS_CREATED).all()
        _logger.debug("Found %d tasks to process", len(all_tasks))
        for task in all_tasks:
            try:
                crawler_name = task.kind
                options = json.loads(task.options)
                options = options.copy()
                options["crawler"] = crawler_name
                options["task_id"] = task.task_id

                # get the fixed options on the settings that will be aggregated
                # with the options sent on the table.
                default_settings = settings.DAVINCI_CONF["crawler-params"].get("default", {})
                crawler_settings = settings.DAVINCI_CONF["crawler-params"].get(crawler_name, {})

                _add_default_options(options, crawler_settings)
                _add_default_options(options, default_settings)

                # fixed options, place here all the fixed options
                options["current_execution_date"] = datetime.utcnow()

                params = json.loads(task.params)

                tasks_queue.put([params, options])
                update_task_status(task, STATUS_QUEUED)
            except Exception as e:
                update_task_status(task, STATUS_FAULTY, source="crawl command", more_info=traceback.format_exc())
                _logger.error("Error while adding params to queue", e)
        time.sleep(interval)
        if times_to_run:
            times_run += 1


def start_crawl(workers_num, interval, times_to_run=None, initialize_consumer=True):
    """
    Run the necessary methods to start crawling data. This method will start a
    tasks pool that will constantly get lines from DB and if anything is new
    will send to a queue that will be read by a consumer.
    Args:
        workers_num: The quantity of workers to start.
        interval: Interval to wait between pool the tasks.
        times_to_run: used on tests to determine that the threads will not run
        forever.
        initialize_consumer: if true the consumer will be initialized, if not
        the consumer will not start and only the tasks will be queued
    """
    crawl_consumer = None
    if initialize_consumer:
        crawl_consumer = CrawlConsumer(workers_num, times_to_run)
        _logger.info("Starting a consumer of %d processes" % workers_num)
        crawl_consumer.start()
    task_thread = Thread(target=_pool_tasks, args=(interval, times_to_run))

    try:
        task_thread.start()
    except TimeoutError:
        _logger.error("Timeout error")
    finally:
        task_thread.join()
        if crawl_consumer:
            crawl_consumer.join()


class Command(BaseCommand):
    help = "Start all the necessary methods to start crawling the database"

    def __init__(self):
        super().__init__()
        self._parser = CommandParser(
            description="Task Pool settings",
            formatter_class=DjangoHelpFormatter,
            missing_args_message=getattr(self, "missing_args_message", None),
            called_from_command_line=getattr(self, "_called_from_command_line", None),
        )

        self._parser.add_argument(
            "--workers-num",
            required=False,
            action="store",
            dest="workers_num",
            default=10,
            type=int,
            help="The number of workers (threads) to launch in parallel",
        )
        self._parser.add_argument(
            "--interval",
            required=False,
            action="store",
            dest="interval",
            default=5,
            type=int,
            help="Interval to wait between pool the tasks",
        )
        self._parser.add_argument(
            "--settings",
            help=(
                "The Python path to a settings module, e.g. "
                '"myproject.settings.main". If this isn\'t provided, the '
                "DJANGO_SETTINGS_MODULE environment variable will be used."
            ),
        )
        self._parser.add_argument(
            "--pythonpath", help="A directory to add to the Python path, e.g. " '"/home/djangoprojects/myproject".',
        )
        self._parser.add_argument(
            "--no-color", action="store_true", dest="no_color", help="Don't colorize the command output.",
        )
        self._parser.add_argument(
            "--force-color", action="store_true", help="Force colorization of the command output.",
        )

    def run_from_argv(self, argv):
        _logger.info("Starting to crawl")

        parser = self._parser
        options, known_args = parser.parse_known_args(argv[2:])

        cmd_options = vars(options)
        args = cmd_options.pop("args", ())
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
                self.stderr.write("%s: %s" % (e.__class__.__name__, e))
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

        start_crawl(workers_num, interval)
