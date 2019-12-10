# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import os

import django
from _datetime import datetime
from abc import ABCMeta
import abc
import logging

from davinci_crawling.proxy.proxy import ProxyManager
from django.conf import settings

from django.core.management import CommandParser
from django.core.management.base import DjangoHelpFormatter

from davinci_crawling.time import mk_datetime

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


_logger = logging.getLogger("davinci_crawling")


def get_configuration(crawler_name):
    return settings.DAVINCI_CRAWLERS[crawler_name] \
        if crawler_name in settings.DAVINCI_CRAWLERS else {}


class Crawler(metaclass=ABCMeta):

    CHROME_DESIREDCAPABILITIES = "chrome_desired_capabilities"

    proxy_manager = ProxyManager()

    # The unique name of the crawler to be identified in the system
    __crawler_name__ = None

    def __init__(self) -> None:
        super().__init__()

        if not hasattr(self, "__crawler_name__"):
            raise RuntimeError(
                "The crawler {} must specify "
                "class Meta attribute '__crawler_name__'".
                format(self.__class__))

        self.__prepare_parser()

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
        path = os.path.dirname(os.path.abspath(__file__))
        if chromium_file:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-features=NetworkService")

            proxy_address = cls.proxy_manager.get_proxy_address()

            chrome_options.binary_location = chromium_file

            capabilities = DesiredCapabilities.CHROME

            if Crawler.CHROME_DESIREDCAPABILITIES in options:
                for key, value in options[
                        Crawler.CHROME_DESIREDCAPABILITIES].items():
                    capabilities[key] = value

            if proxy_address:
                driver = webdriver.Chrome(
                    chrome_options=chrome_options,
                    desired_capabilities=capabilities,
                    seleniumwire_options=proxy_address)
            else:
                driver = webdriver.Chrome(
                    chrome_options=chrome_options,
                    desired_capabilities=capabilities)

            _logger.info("Using CHROMIUM as Dynamic Web Driver. Driver {}".
                         format(repr(driver)))
        else:
            # PhantomJS folder
            phantomjs_path = options.get("phantomjs_path", None)
            if phantomjs_path:
                driver = webdriver.PhantomJS(
                    executable_path=phantomjs_path)
                _logger.info("Using PHANTOMJS as Dynamic Web Driver. Driver "
                             "{}".format(repr(driver)))

        if not driver:
            _logger.warning("No Dynamic Web Driver loaded!!! "
                            "(no Chromium neither PhantomJS specified)")

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
            prog='%s' % getattr(self, "__crawler_name__"),
            description="Crawler settings",
            formatter_class=DjangoHelpFormatter,
            missing_args_message=getattr(self, 'missing_args_message', None),
            called_from_command_line=getattr(
                self, '_called_from_command_line', None),
        )
        self._parser.add_argument(
            '--version',
            action='version',
            version=self.__get_version())
        self._parser.add_argument(
            '-v',
            '--verbosity',
            action='store',
            dest='verbosity',
            default=1,
            type=int, choices=[0, 1, 2, 3],
            help='Verbosity level; 0=minimal output, 1=normal output, '
                 '2=verbose output, 3=very verbose output',
        )
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
            '--traceback',
            action='store_true',
            help='Raise on CommandError exceptions')
        self._parser.add_argument(
            '--no-color',
            action='store_true', dest='no_color',
            help="Don't colorize the command output.",
        )
        self._parser.add_argument(
            '--force-color', action='store_true',
            help='Force colorization of the command output.',
        )

        # Cache storage
        # In production this folder could be volatile, losing all the data
        # when the crawler finish. You can use the database or GCP to
        # save permanently files or content
        self._parser.add_argument(
            '--cache-dir',
            required=False,
            action='store',
            dest='cache_dir',
            default="fs:///data/harvest/permanent",
            type=str,
            help="The path where we will leave the files."
                 " Ex. fs:///data/harvest/permanent"
                 "     gs://davinci_harvest")

        # Local path for manipulate files. This storage is volatile in nature.
        self._parser.add_argument(
            '--local-dir',
            required=False,
            action='store',
            dest='local_dir',
            default="fs///data/harvest/volatile",
            type=str,
            help="The path where we will leave the files."
                 " Ex. fs///data/harvest/volatile")

        # Parallel Workers
        self._parser.add_argument(
            '--workers-num',
            required=False,
            action='store',
            dest='workers_num',
            default=10,
            type=int,
            help="The number of workers (threads) to launch in parallel")

        # Location of the bin folder of the PhantomJS library
        self._parser.add_argument(
            '--phantomjs-path',
            required=False,
            action='store',
            dest='phantomjs_path',
            default=None,
            type=str,
            help="Absolute path to the bin directory of the PhantomJS library."
                 "Ex. '/phantomjs-2.1.1-macosx/bin/phantomjs'")

        # Location of the bin folder of the PhantomJS library
        self._parser.add_argument(
            '--chromium-bin-file',
            required=False,
            action='store',
            dest='chromium_bin_file',
            default=None,
            type=str,
            help="Absolute path to the Chromium bin file."
                 "Ex. '/Applications/Chromium.app/Contents/MacOS/Chromium'")

        # GCP Project
        self._parser.add_argument(
            '--io-gs-project',
            required=False,
            action='store',
            dest='io_gs_project',
            default=None,
            type=str,
            help="If we are using Google Storage to persist the files, we "
                 " could need to inform about the project of the bucket."
                 "Ex. centering-badge-212119")

        # Current execution time
        self._parser.add_argument(
            '--current-execution-date',
            required=False,
            action='store',
            dest='current_execution_date',
            default=datetime.utcnow(),
            type=mk_datetime,
            help="The current time we are starting the crawler (UTC)"
                 " Ex. '2008-09-03T20:56:35.450686Z")

        # Last execution time
        self._parser.add_argument(
            '--last-execution-date',
            required=False,
            action='store',
            dest='last_execution_date',
            default=None,
            type=mk_datetime,
            help="The last time we executed the crawler (UTC)"
                 " Ex. '2007-09-03T20:56:35.450686Z")

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
