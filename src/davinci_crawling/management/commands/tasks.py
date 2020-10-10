# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
import sys

from caravaggio_rest_api.sub_commander import CaravaggioBaseCommand


class Command(CaravaggioBaseCommand):
    sub_commands = {
        "run_on_demand": "run_on_demand",
    }

    def _get_current_parent_module(self):
        this_module = sys.modules[__name__].__name__
        parent_module = ".".join(this_module.split(".")[:-1])
        return parent_module
