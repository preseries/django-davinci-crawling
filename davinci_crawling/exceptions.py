# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL


class DownloadException(Exception):

    url = None

    def __init__(self, url):
        self.url = url
