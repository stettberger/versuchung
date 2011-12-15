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

