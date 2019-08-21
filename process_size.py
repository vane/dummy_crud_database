#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import os
import psutil

def convert_size(size_bytes, index=0):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    if not index:
        index = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, index)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[index])

def get_size():
    process = psutil.Process(os.getpid())
    return convert_size(process.memory_info().rss, 2)
