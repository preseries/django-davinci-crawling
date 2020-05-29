# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import json

import os

import django
from _datetime import datetime
from abc import ABCMeta
import abc
import logging

from caravaggio_rest_api.haystack.backends.utils import CaravaggioSearchPaginator
from davinci_crawling.management.commands.utils.utils import update_task_status

from davinci_crawling.task.models import Task, STATUS_FAULTY, STATUS_MAINTENANCE, TaskMoreInfo
from davinci_crawling.proxy.proxy import ProxyManager
from django.conf import settings

from django.core.management import CommandParser
from django.core.management.base import DjangoHelpFormatter

from davinci_crawling.time import mk_datetime
from django.test import RequestFactory
from django.utils import timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from davinci_crawling.entity_diff.diff import make_diff
from solrq import Q

_logger = logging.getLogger("davinci_crawling")

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-gpu")
CHROME_OPTIONS.add_argument("--disable-features=NetworkService")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")


def get_configuration(crawler_name):
    return settings.DAVINCI_CRAWLERS[crawler_name] if crawler_name in settings.DAVINCI_CRAWLERS else {}


class Crawler(metaclass=ABCMeta):

    CHROME_DESIREDCAPABILITIES = "chrome_desired_capabilities"

    defaults_parser = {
        "verbosity": 1,
        "cache_dir": "fs:///data/harvest/permanent",
        "local_dir": "fs:///data/harvest/volatile",
        "workers_num": 10,
    }

    proxy_manager = ProxyManager()

    # The unique name of the crawler to be identified in the system
    __crawler_name__ = None

    # The serializer class that is used to transform the model to json
    __serializer_class__ = None

    def __init__(self) -> None:
        super().__init__()

        if not hasattr(self, "__crawler_name__"):
            raise RuntimeError(
                "The crawler {} must specify " "class Meta attribute '__crawler_name__'".format(self.__class__)
            )

        if not hasattr(self, "__serializer_class__"):
            raise RuntimeError(
                "The crawler {} must specify " "class Meta attribute '__serializer_class__'".format(self.__class__)
            )

        if hasattr(settings, "DAVINCI_CONF") and "crawler-params" in settings.DAVINCI_CONF:
            crawler_params = settings.DAVINCI_CONF["crawler-params"]
            if "default" in crawler_params:
                self.defaults_parser.update(crawler_params["default"])

            if self.__crawler_name__ in crawler_params:
                self.defaults_parser.update(crawler_params[self.__crawler_name__])

        self.__prepare_parser()
        if self.__serializer_class__:
            self.serializer = self.__serializer_class__(context={"request": self._get_fake_request()})

    @classmethod
    def get_web_driver(cls, **options):
        """
        Initialized the Web Driver to allow dynamic web processing

        :param options:
        :return: the driver informed in the options (chromium has preference)
        """

        driver = None

        # Chromium folder
        chromium_file = options.get("chromium_bin_file", None)
        use_proxy = options.pop("use_proxy", True)
        path = os.path.dirname(os.path.abspath(__file__))
        if chromium_file:
            proxy_address = cls.proxy_manager.get_proxy_address()
            if use_proxy and proxy_address:
                proxy_address = proxy_address["http"].replace("http://", "")
                CHROME_OPTIONS.add_argument("--proxy-server=%s" % proxy_address)

            CHROME_OPTIONS.binary_location = chromium_file

            capabilities = DesiredCapabilities.CHROME

            if Crawler.CHROME_DESIREDCAPABILITIES in options:
                for key, value in options[Crawler.CHROME_DESIREDCAPABILITIES].items():
                    capabilities[key] = value

            driver = webdriver.Chrome(chrome_options=CHROME_OPTIONS, desired_capabilities=capabilities)

            _logger.info("Using CHROMIUM as Dynamic Web Driver. Driver {}".format(repr(driver)))
        else:
            # PhantomJS folder
            phantomjs_path = options.get("phantomjs_path", None)
            if phantomjs_path:
                driver = webdriver.PhantomJS(executable_path=phantomjs_path)
                _logger.info("Using PHANTOMJS as Dynamic Web Driver. Driver " "{}".format(repr(driver)))

        if not driver:
            _logger.warning("No Dynamic Web Driver loaded!!! " "(no Chromium neither PhantomJS specified)")

        return driver

    def __get_version(self):
        """
        Return the Django version, which should be correct for all built-in
        Django commands. User-supplied commands can override this method to
        return their own version.
        """
        return django.get_version()

    def __prepare_parser(self):
        """
        Create and return the ``ArgumentParser`` which will be used to
        parse the arguments to this command.
        """
        self._parser = CommandParser(
            prog="%s" % getattr(self, "__crawler_name__"),
            description="Crawler settings",
            formatter_class=DjangoHelpFormatter,
            missing_args_message=getattr(self, "missing_args_message", None),
            called_from_command_line=getattr(self, "_called_from_command_line", None),
        )
        self._parser.add_argument("--version", action="version", version=self.__get_version())
        self._parser.add_argument(
            "-v",
            "--verbosity",
            action="store",
            dest="verbosity",
            default=self.defaults_parser.get("verbosity", None),
            type=int,
            choices=[0, 1, 2, 3],
            help="Verbosity level; 0=minimal output, 1=normal output, " "2=verbose output, 3=very verbose output",
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
        self._parser.add_argument("--traceback", action="store_true", help="Raise on CommandError exceptions")
        self._parser.add_argument(
            "--no-color", action="store_true", dest="no_color", help="Don't colorize the command output.",
        )
        self._parser.add_argument(
            "--force-color", action="store_true", help="Force colorization of the command output.",
        )

        # Cache storage
        # In production this folder could be volatile, losing all the data
        # when the crawler finish. You can use the database or GCP to
        # save permanently files or content
        self._parser.add_argument(
            "--cache-dir",
            required=False,
            action="store",
            dest="cache_dir",
            default=self.defaults_parser.get("cache_dir", None),
            type=str,
            help="The path where we will leave the files."
            " Ex. fs:///data/harvest/permanent"
            "     gs://davinci_harvest",
        )

        # Local path for manipulate files. This storage is volatile in nature.
        self._parser.add_argument(
            "--local-dir",
            required=False,
            action="store",
            dest="local_dir",
            default=self.defaults_parser.get("local_dir", None),
            type=str,
            help="The path where we will leave the files." " Ex. fs///data/harvest/volatile",
        )

        # Parallel Workers
        self._parser.add_argument(
            "--workers-num",
            required=False,
            action="store",
            dest="workers_num",
            default=self.defaults_parser.get("workers_num", None),
            type=int,
            help="The number of workers (threads) to launch in parallel",
        )

        # Location of the bin folder of the PhantomJS library
        self._parser.add_argument(
            "--phantomjs-path",
            required=False,
            action="store",
            dest="phantomjs_path",
            default=self.defaults_parser.get("phantomjs_path", None),
            type=str,
            help="Absolute path to the bin directory of the PhantomJS library."
            "Ex. '/phantomjs-2.1.1-macosx/bin/phantomjs'",
        )

        # Location of the bin folder of the PhantomJS library
        self._parser.add_argument(
            "--chromium-bin-file",
            required=False,
            action="store",
            dest="chromium_bin_file",
            default=self.defaults_parser.get("chromium_bin_file", None),
            type=str,
            help="Absolute path to the Chromium bin file." "Ex. '/Applications/Chromium.app/Contents/MacOS/Chromium'",
        )

        # GCP Project
        self._parser.add_argument(
            "--io-gs-project",
            required=False,
            action="store",
            dest="io_gs_project",
            default=self.defaults_parser.get("io_gs_project", None),
            type=str,
            help="If we are using Google Storage to persist the files, we "
            " could need to inform about the project of the bucket."
            "Ex. centering-badge-212119",
        )

        # Current execution time
        self._parser.add_argument(
            "--current-execution-date",
            required=False,
            action="store",
            dest="current_execution_date",
            default=datetime.utcnow(),
            type=mk_datetime,
            help="The current time we are starting the crawler (UTC)" " Ex. '2008-09-03T20:56:35.450686Z",
        )

        # Last execution time
        self._parser.add_argument(
            "--last-execution-date",
            required=False,
            action="store",
            dest="last_execution_date",
            default=None,
            type=mk_datetime,
            help="The last time we executed the crawler (UTC)" " Ex. '2007-09-03T20:56:35.450686Z",
        )

        self.add_arguments(self._parser)

    def get_parser(self):
        return self._parser

    def add_arguments(self, parser):
        pass

    @abc.abstractmethod
    def crawl_params(self, producer, **options):
        raise NotImplementedError()

    @abc.abstractmethod
    def crawl(self, task_id, crawling_params, options):
        raise NotImplementedError()

    def error(self, task_id, more_info=None):
        """
        Change the task (with the task_id) to the error status and also add
        the more_info to the more_info of the task.
        Args:
            task_id: The task id to add the error
            more_info: more information about the error
        """
        update_task_status(task_id, STATUS_FAULTY, source=self.__crawler_name__, more_info=more_info)

    def maintenance_notice(self, task_id, more_info=None):
        """
        Create a new task on the DB with the status maintenance, that signals
        that something is wrong with that task but we can continue processing
        it.

        This can be used for example to signal that the structure of some api
        changed.
        Args:
            task_id: The task id to notice
            more_info: more information about the maintenance notice
        """
        task = Task.objects.get(task_id=task_id)

        if not task:
            raise Exception("Not found task with task id %s", task_id)

        task_data = {
            "status": STATUS_MAINTENANCE,
            "kind": task.kind,
            "options": task.options,
            "params": task.params,
            "type": task.type,
            "user": task.user,
            "more_info": [
                TaskMoreInfo(**{"source": self.__crawler_name__, "created_at": timezone.now(), "details": more_info})
            ],
        }

        Task.create(**task_data)

    @staticmethod
    def _get_fake_request():
        return RequestFactory().get("./fake_path")

    def _object_to_dict(self, instance, serializer_class):
        if serializer_class:
            serializer = serializer_class(context={"request": self._get_fake_request()})
        else:
            serializer = self.serializer
        return serializer.to_representation(instance, use_cache=False)

    def register_differences(
        self, previous_object=None, current_object=None, already_computed_diff=None, task_id=None, serializer_class=None
    ):
        """
        This method is used to register the differences between two "resources"
        on the DB that the task_id generated, this method will use the jsondiff
        implementation that will compare the two objects and generate a diff.
        Once the diff is generated we will write it on the Task table on the
        task that has the task_id that was passed on this method, there we will
        have three fields, the `differences_from_last_version` that have all
        the changes that occurred and the `updated_fields`, `deleted_fields`,
        `inserted_fields` and `changed_fields` that contains all the fields
        that have been changed.

        There are two ways to generate these differences, you can pass the two
        objects `previous_object` and `current_object` or you can add the
        `already_computed_diff` with the diff that you already calculated, the
        `already_computed_diff` dict should contains four main keys, that are
        the `all` that goes to the `differences_from_last_version` field and
        the `inserts`, `updates`, `deletes` and `changes` that goes to:
        inserted_fields, updated_fields, deleted_fields and `changed_fields`.

        IMPORTANT: if you have a complex structure on your object, like: a list
        of objects you'll need to sort that list to guarantee that every time
        this method is called we have the list on the same order, if the order
        changes the jsondiff lib could generate a wrong output.
        Args:
            previous_object: the previous version of the object used to
                compare.
            current_object: the current version of the object used to compare.
            already_computed_diff: if the diff is already computed this will be
                the result of the diff on dict format.
            task_id: the task id that generated the current_object and where we
            will store the result of the diff.
            serializer_class: if you want to specify another serializer class
                different from self.__serializer_class__ you can do on this
                variable.
        """
        if task_id is None:
            raise Exception("Task id couldn't be None")

        if previous_object is None and current_object is None and already_computed_diff is None:
            raise Exception("You should specify at least the objects or the " "computed diff")

        if not already_computed_diff:
            previous_dict = self._object_to_dict(previous_object, serializer_class)
            current_object_dict = self._object_to_dict(current_object, serializer_class)

            diff = make_diff(previous_dict, current_object_dict)
        else:
            diff = already_computed_diff

        all_diff = diff["all"]

        inserted_fields = diff["inserts"]
        updated_fields = diff["updates"]
        deleted_fields = diff["deletes"]
        changed_fields = set()
        changed_fields.update(inserted_fields, updated_fields, deleted_fields)
        changed_fields = list(changed_fields)

        task = Task.objects.get(task_id=task_id)

        if not task:
            raise Exception("Not found task with task id {}".format(str(task_id)))

        task.update(
            **{
                "differences_from_last_version": json.dumps(all_diff),
                "inserted_fields": inserted_fields,
                "updated_fields": updated_fields,
                "deleted_fields": deleted_fields,
                "changed_fields": changed_fields,
            }
        )
