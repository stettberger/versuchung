#!/usr/bin/python

class JavascriptStyleDictAccess(dict):
    def __init__(self, d):
        self.update(d)
    def __getattribute__(self, name):
        try:
            return dict.__getattribute__(self, name)
        except AttributeError:
            pass
        name = name.replace("_", "-")
        if name in self:
            return self[name]
        raise AttributeError

import logging


def setup_logging(log_level):
    """ setup the logging module with the given log_level """

    l = logging.WARNING # default
    if log_level == 1:
        l = logging.INFO
    elif log_level >= 2:
        l = logging.DEBUG

    logging.basicConfig(level=l)
