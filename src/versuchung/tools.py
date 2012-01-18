#!/usr/bin/python
import logging

class JavascriptStyleDictAccess(dict):
    def __init__(self, d):
        self.update(d)
    def __getattribute__(self, name):
        try:
            return dict.__getattribute__(self, name)
        except AttributeError:
            pass
        if name in self:
            return self[name]
        name = name.replace("_", "-")
        if name in self:
            return self[name]
        raise AttributeError



def setup_logging(log_level):
    """ setup the logging module with the given log_level """

    l = logging.WARNING # default
    if log_level == 1:
        l = logging.INFO
    elif log_level >= 2:
        l = logging.DEBUG

    logging.basicConfig(level=l)

def before(decorator_argument):
    """Decorator for executing functions before other functions"""
    def decorator(func):
        def wrapped(self, *args, **kwargs):
            # Late binding
            inb4 = decorator_argument
            if type(decorator_argument) == str:
                inb4 = getattr(self, decorator_argument)

            if "func_code" in dir(inb4):
                argcount = inb4.func_code.co_argcount
            else:
                raise RuntimeError("Invalid argument to decorator")

            if argcount == 1:
                inb4(self)
            elif argcount == 0:
                inb4()
            else:
                raise RuntimeError("Unexpected parameter count")

            return func(self, *args, **kwargs)
        return wrapped
    return decorator

