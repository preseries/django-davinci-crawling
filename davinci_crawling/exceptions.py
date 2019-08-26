# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.


class DownloadException(Exception):

    url = None

    def __init__(self, url):
        self.url = url
