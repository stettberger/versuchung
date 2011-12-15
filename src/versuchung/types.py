#!/usr/bin/python

import os

class Type(object):
    """This is the base type for all input and output parameters"""
    @property
    def name(self):
        return self.__name
    @name.setter
    def name(self, name):
        self.__name = name

    def value(self):
        """Default accessor for this kind of data"""
        raise NotImplemented

    @property
    def base_directory(self):
        return self.__base_directory
    @base_directory.setter
    def base_directory(self, value):
        self.__base_directory = value

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


class String(InputParameter):
    def __init__(self, default_value=""):
        self.__value = default_value

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__value)
    def inp_extract_cmdline_parser(self, opts, args):
        self.__value = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.__value}

    def value(self):
        return self.__value

class File(InputParameter, OutputParameter):
    def __init__(self, default_filename=""):
        self.__filename = default_filename
        self.__value = ""

    @property
    def filename(self):
        return os.path.join(self.base_directory, self.__filename)

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__filename)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__filename = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.__filename}

    def value(self):
        if not self.__value:
            with open(self.filename) as fd:
                self.__value = fd.read()
        return self.__value

    def write(self, content, append = False):
        if append:
            self.__value += content
        else:
            self.__value = content

    def outp_setup_output(self):
        pass

    def outp_tear_down_output(self):
        with open(os.path.join(self.base_directory, self.filename), "w+") as fd:
            if self.__value is None:
                self.__value = ""
            fd.write(self.__value)

