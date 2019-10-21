# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
import multiprocessing


class NoDaemonProcess(multiprocessing.Process):
    """
    Creates a non-daemon process so we can be able to start a pool inside
    another pool.

    https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
    """
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)


class NoDaemonPool(multiprocessing.pool.Pool):
    """
    A pool that doesn't use a daemon process, this is necessary to start pool
    inside a pool.

    https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
    """
    Process = NoDaemonProcess
