# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL
import logging
import os

from django.conf import settings
from django.utils import timezone

from davinci_crawling.crawler import get_configuration
from davinci_crawling.gcp.instances import GCPComputeService

_logger = logging.getLogger("davinci_crawling.scheduler")


def crawling_job(crawler_name):
    """Scheduler of a Crawling Job

    """
    crawler_config = get_configuration(crawler_name)

    now = timezone.now()

    _logger.debug("Executing crawling job for {} at {}.".
                  format(crawler_name, str(now)))

    params = {}
    params.update(crawler_config.get("arguments", {}))

    base_config_keys = ["--current-date", "--verbosity",
                        "--workers-num", "--cache-dir", "--local-dir"]

    current_date = params.get(
        "--current-date", now.utcnow().strftime("%Y-%m-%d %H:%M:%S.%fZ"))
    verbosity = params.get("--verbosity", "0")
    workers_num = params.get("--workers-num", "5")
    cache_dir = params.get("--cache-dir", "gs://davinci_cache")
    local_dir = params.get(
        "--local-dir", "fs:///data/harvest/local")

    if hasattr(settings, "DAVINCI_CRAWLERS_ENV_PARAMS"):
        for param_name in settings.DAVINCI_CRAWLERS_ENV_PARAMS:
            if param_name not in params:
                if param_name in os.environ:
                    params[param_name] = os.environ[param_name]
                else:
                    _logger.warning(
                        "The variable {} is not available in the "
                        "environment.".format(param_name))
            else:
                _logger.warning(
                    "The environment variable {} has been redefined in the "
                    "crawler settings section. Environment value: {}. "
                    "Settings value: {}".format(
                        param_name,
                        os.environ[param_name],
                        params[param_name]))

    for base_key in base_config_keys:
        if base_key in params:
            del params[base_key]

    try:
        compute_service = GCPComputeService.get()
        instance = compute_service.commission_instance(
            settings.PROJECT_DOCKER_IMAGE,
            crawler_name,
            current_date,
            verbosity,
            workers_num,
            cache_dir,
            local_dir,
            params)

        compute_service.wait_for_operation(crawler_name)

        _logger.debug("Crawling job for {} executed. Instance: {}.".
                      format(crawler_name, instance))
    except Exception as ex:
        _logger.error(
            "Unable to execute the crawler {}".format(crawler_name), ex)
        raise ex
