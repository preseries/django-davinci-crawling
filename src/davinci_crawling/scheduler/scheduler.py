# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
# http://en.wikipedia.org/wiki/Cron

import logging
from django.conf import settings

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.jobstores import register_events

from davinci_crawling.scheduler import crawling_job

_logger = logging.getLogger("davinci_crawling.scheduler")


class Scheduler:

    instance = None

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    def __init__(self):
        self.scheduler = None

    def is_initialized(self):
        return self.scheduler is not None

    def is_running(self):
        return self.scheduler is not None

    def stop_schedule(self):
        try:
            if self.is_running():
                self.scheduler.shutdown()
                self.scheduler = None
                return True
        except (KeyboardInterrupt, SystemExit):
            _logger.exception("Unable to stop the scheduler")
            pass
            return False

        return True

    def start_schedule(self):
        try:
            if not self.is_running():
                self.initialize()
                return True
        except (KeyboardInterrupt, SystemExit):
            _logger.exception("Unable to start the scheduler")
            pass
            return False

        return True

    def initialize(self):
        # Do nothing if the scheduler is already running
        if self.is_running():
            return

        if settings.DEBUG:
            self.scheduler = BackgroundScheduler(daemon=False)
        else:
            self.scheduler = BackgroundScheduler()

        executors = {
            'default': {'type': 'threadpool', 'max_workers': 3},
            'processpool': ProcessPoolExecutor(max_workers=3)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 2
        }

        job_stores = {
            'default': {'class': DjangoJobStore}
        }

        self.scheduler.configure(executors=executors,
                                 job_defaults=job_defaults,
                                 jobstores=job_stores)

        register_events(self.scheduler)

        try:
            # Add configured jobs to scheduler
            if hasattr(settings, "DAVINCI_CRAWLERS"):
                for name, conf in settings.DAVINCI_CRAWLERS.items():
                    if not self.scheduler.get_job(name):
                        if "cron" in conf:
                            _logger.info(
                                "Registering the Crawling Job for: {}".
                                format(name))
                            cron = conf["cron"].split()
                            trigger = CronTrigger(month=cron[3], day=cron[2],
                                                  day_of_week=cron[4],
                                                  hour=cron[1],
                                                  minute=cron[0])
                            self.scheduler.add_job(
                                crawling_job,
                                trigger=trigger,
                                id=name,
                                name=name,
                                args=[name])
                        else:
                            _logger.info(
                                "The Crawler {} do not have schedule details.".
                                format(name))

                if settings.DEBUG:
                    self.scheduler.print_jobs()

                self.scheduler.start()
            else:
                _logger.info("No crawlers registered for automatic crawling")
        except (KeyboardInterrupt, SystemExit):
            _logger.exception("Unable to initialize the scheduler")
            pass
