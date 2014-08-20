# This file is part of versuchung.
# 
# versuchung is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# versuchung is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# versuchung.  If not, see <http://www.gnu.org/licenses/>.

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
        wrapped.__doc__ = func.__doc__
        return wrapped
    return decorator


class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance


class AdviceManager(Singleton):
    def __init__(self):
        if not "before" in dir(self):
            self.before = dict()
            self.around = dict()
            self.after = dict()

    def around_wrapper(self, func, last = None):
        def wrapped(args, kwargs):
            if last:
                return func(last, args, kwargs)
            else:
                return func(*args, **kwargs)
        return wrapped

    @staticmethod
    def advicable(func):
        """Decorator to mark a function as advicable"""
        if not "func_name" in dir(func):
            raise ValueError("No function adviced")
        full_name = "%s.%s" % (func.__module__, func.func_name)

        self = AdviceManager()

        if full_name in self.before:
            raise RuntimeError("Function already marked as advicable")
        self.before[full_name] = []
        self.around[full_name] = []
        self.after[full_name] = []

        def wrapped(*args, **kwargs):
            am = AdviceManager()
            for f in am.before[full_name]:
                ret = f(args, kwargs)
                if ret:
                    (args, kwargs) = ret

            if len(am.around[full_name]) > 0:
                func_ = am.around_wrapper(func, None)
                for f in am.around[full_name]:
                    func_ = am.around_wrapper(f, func_)

                ret = func_(args, kwargs)
            else:
                ret = func(*args, **kwargs)

            for f in am.after[full_name]:
                ret = f(ret)

            return ret
        wrapped.__doc__ = func.__doc__
        return wrapped


class Advice:
    def __init__(self, method, enabled = False):
        self.method = method
        am = AdviceManager()
        self.am = am
        if not method in am.before:
            raise RuntimeError("Function was not marked @advicable")
        self.enabled = False
        if enabled:
            self.enable()

    def disable(self):
        am = self.am
        am.before[self.method] = [ x for x in am.before[self.method]
                                   if x != self.before ]
        am.around[self.method] = [ x for x in am.around[self.method]
                                   if x != self.around ]
        am.after[self.method] = [ x for x in am.after[self.method]
                                  if x != self.after ]

    def enable(self):
        am = self.am
        if self.enabled:
            return
        # Hook only in if the methods are overwritten
        if self.before.im_func != Advice.before.im_func:
            am.before[self.method].append(self.before)
        if self.around.im_func != Advice.around.im_func:
            am.around[self.method].append(self.around)
        if self.after.im_func != Advice.after.im_func:
            am.after[self.method].append(self.after)
        self.enabled = True

    def before(self, args, kwargs):
        return (args, kwargs)
    def around(self, func, args, kwargs):
        return func(args, kwargs)
    def after(self, ret):
        return ret

