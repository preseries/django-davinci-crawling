# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
from task.models import Task


def update_task_status(task, status):
    if not isinstance(task, Task):
        task = Task.objects.filter(task_id=task).first()

    task.update(**{"status": status})
