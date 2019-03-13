# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL
import logging

from django.conf import settings
from django.utils import timezone

from davinci_crawling.crawler import get_configuration
from davinci_crawling.gcp.instances import GCPComputeService

_logger = logging.getLogger("davinci_crawling.scheduler")


# def can_be_fired(etl_process):
#    """
#    We need to check the if the parent workflows has been executed and finished
#    before fire this process.
#
#    To do so we need to convert the names of the etlprocesses into the internal
#    workflow names used in the Pipeline Workflow Context control structures.
#    """
#
#    try:
#        context_wf = etl_process.get_pipeline().get_name()
#        parent_wfs = etl_process.get_parents()
#
#        if len(parent_wfs) == 0:
#            return True
#
#        LOGGER.debug("------------------------------------------")
#
#        LOGGER.debug("WF to check: %s" % context_wf)
#
#        context_parent_wfs = [Pipeline.get_wf_name(wf_name)
#                               for wf_name in parent_wfs]
#
#        LOGGER.debug("Parents to check: %s" % ",".join(context_parent_wfs))
#
#
#        client = MongoClient(ETLPROCESS_MONGO_URL)
#        db = client.get_default_database()
#        collection = db.get_collection('wf_context')
#
#        # The last time the current workflow was successfully executed
#        # (SaveContextTask was executed at the end of the wk)
#        last_execution_date = \
#            collection.find_one({'__wf_name': context_wf},
#                                {"last_execution_date": 1})
#
#        if last_execution_date is None:
#            LOGGER.debug("WF last execution date: NEVER FIRED BEFORE")
#
#
#            fired_parents = \
#                collection.find({'__wf_name': {"$in": context_parent_wfs}},
#                                {"__wf_name": 1})
#
#            if fired_parents.count() < len(context_parent_wfs):
#                fired_parents_name = [fired_parent["__wf_name"]
#                                      for fired_parent in fired_parents]
#
#                LOGGER.info("The process [%s] cannot be executed because "
#                            "the some parents have not been executed "
#                            "yet: [%s]" %
#                            (etl_process.client_name,
#                            ",".join([
#                                context_parent_wf for context_parent_wf in
#                                context_parent_wfs
#                                if context_parent_wf
#                                   not in fired_parents_name])))
#                return False
#            else:
#                LOGGER.info("The process [%s] can be executed because "
#                            "all the following parents have been executed "
#                            "at least once. Processes: %s" %
#                            (etl_process.client_name,
#                            ",".join([
#                                context_parent_wf for
#                                context_parent_wf in context_parent_wfs])))
#
#        else:
#            LOGGER.debug("WF last execution date: %s" %
#                         last_execution_date["last_execution_date"].
#                         strftime("%Y-%m-%d %H:%M:%S"))
#
#            # Look for the parent workflows that haven't been executed yet. All the
#            # parent workflows must have a "last_execution_date" greater than the
#            # "last_execution_date" of the process we want to run now
#            # Look for the parent process that still needs to be fired
#            pending_parents = \
#                collection.find({'__wf_name': {"$in": context_parent_wfs},
#                                 "last_execution_date": {
#                                     "$lte":
#                                         last_execution_date["last_execution_date"]
#                                 }}, {"__wf_name": 1})
#
#            if pending_parents.count() > 0:
#                LOGGER.info("The process [%s] cannot be executed because "
#                            "the following parents have not been executed "
#                            "yet: [%s]" %
#                            (etl_process.client_name,
#                            ",".join([pending_parent["__wf_name"]
#                                      for pending_parent in pending_parents])))
#                return False
#            else:
#                LOGGER.info("The process [%s] can be executed because "
#                            "the following parents have been executed "
#                            "after than [%s]: [%s]" %
#                            (etl_process.client_name,
#                            last_execution_date["last_execution_date"].
#                             strftime("%Y-%m-%d %H:%M:%S"),
#                            ",".join([pending_parent["__wf_name"]
#                                      for pending_parent in pending_parents])))
#
#
#        return True
#    except RuntimeError as ex:
#        LOGGER.error("Unable to check parents. Cause: %s", ex)
#        raise ex


def crawling_job(crawler_name):
    """Scheduler of a Crawling Job

    """
    crawler_config = get_configuration(crawler_name)

    now = timezone.now()

    _logger.debug("Executing crawling job for {} at {}.".
                  format(crawler_name, str(now)))

    compute_service = GCPComputeService.get()
    instance = compute_service.commission_instance(
        settings.PRO,
        crawler_name, [
            {"key": "--test-param2", "value": 43},
            {"key": "--current-date", "value": str(now)},
        ])

    compute_service.wait_for_operation(crawler_name)

    _logger.debug("Crawling job for {} executed. Instance: {}.".
                  format(crawler_name, instance))


    #_logger.debug("Executing crawling job for {} at {}.".
    #              format(crawler_name, str(now)))

#    from model.models import PipelineInstance
#
#    pipelines = [pipeline for pipeline in
#                 PipelineInstance.objects.filter(next_execution__lt=now)
#                     .order_by('next_execution')]
#
#    for pipeline in pipelines:
#        if pipeline.is_active:
#            try:
#                etl_process = ETLProcess(pipeline.pipeline_name)
#
#                if can_be_fired(etl_process):
#                    # We only can start the process if the pipeline was not
#                    # already launched. That is, there is no workflow in
#                    # WAITING TO BE EXECUTED or RUNNING
#                    if not etl_process.is_running(LAUNCHPAD) and not \
#                            etl_process.is_waiting(LAUNCHPAD):
#
#                        # The ID of the last executed workflow
#                        wf_id = etl_process.get_last_wf_id(LAUNCHPAD)
#
#                        # Let's start the workflow if it were never started or
#                        #   the last execution was successfully finished
#                        if wf_id is None or \
#                            etl_process.is_completed(LAUNCHPAD) or \
#                                etl_process.is_archived(LAUNCHPAD):
#                            etl_process.start(LAUNCHPAD)
#                            pipeline.save()
#                            LOGGER.debug(
#                                "The etlprocess [%s] has been launched." %
#                                pipeline.pipeline_name)
#                    else:
#                        LOGGER.debug(
#                            "The etlprocess [%s] is already running or "
#                            "waiting to be run by the WF server." %
#                            pipeline.pipeline_name)
#
#            except Exception as e:
#                LOGGER.exception("Scheduler Error. Job: %s. Cause: %s" %
#                                 (pipeline.pipeline_name, e))


#def check_job_status(crawler_name):
#    """Scheduler of a Crawling Job
#
#    """
#    now = timezone.now()
