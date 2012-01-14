#!/usr/bin/python

import os
import csv
from  cStringIO import StringIO

class Type(object):
    """This is the base type for all input and output parameters"""
    @property
    def name(self):
        return self.__name
    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def value(self):
        """Default accessor for this kind of data"""
        raise NotImplemented

    @property
    def base_directory(self):
        return self.__base_directory
    @base_directory.setter
    def base_directory(self, value):
        self.__base_directory = value

    def propagate_meta_data(self, subname, other, fields = ["base_directory", "tmp_directory"]):
        other.name = self.name + "-" + subname
        for field in fields:
            if field in dir(self) and field in dir(other):
                # Copy the value
                setattr(other, field, getattr(self, field))

class InputParameter:
    def inp_setup_cmdline_parser(self, parser):
        raise NotImplemented
    def inp_extract_cmdline_parser(self, opts, args):
        raise NotImplemented

    def __parser_option(self, option = None):
        if option:
            return self.name + "-" + option
        return self.name

    def inp_parser_add(self, parser, option, default):
        option = self.__parser_option(option)
        parser.add_option('', '--%s' % option,
                          dest = option,
                          help = "(default: %s)" % default,
                          default = default)

    def inp_parser_extract(self, opts, option):
        return getattr(opts, self.__parser_option(option), None)

    def inp_metadata(self):
        return {}



class OutputParameter:
    def outp_setup_output(self):
        raise NotImplemented
    def outp_tear_down_output(self):
        raise NotImplemented


class String(InputParameter, Type):
    """Can be used as: **input parameter**

    A String is the most simple input parameter."""

    def __init__(self, default_value=""):
        self.__value = default_value

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__value)
    def inp_extract_cmdline_parser(self, opts, args):
        self.__value = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.value}

    @property
    def value(self):
        """The value of the string. This is either the default value
        or the parameter given on the command line"""
        return self.__value

