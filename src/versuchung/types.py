#!/usr/bin/python

import os
import csv
from  cStringIO import StringIO
from optparse import OptionParser
import copy


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
        if subname != None:
            other.name = "%s-%s" %(self.name, subname)
        else:
            other.name = self.name
        for field in fields:
            if field in dir(self) and field in dir(other):
                # Copy the value
                setattr(other, field, getattr(self, field))

    def before_experiment_run(self, parameter_type):
        pass

    def after_experiment_run(self, parameter_type):
        pass


class InputParameter:
    def __init__(self):
        pass
    def inp_setup_cmdline_parser(self, parser):
        raise NotImplemented
    def inp_extract_cmdline_parser(self, opts, args):
        raise NotImplemented

    def __parser_option(self, option = None):
        if option:
            return self.name + "-" + option
        return self.name

    def inp_parser_add(self, parser, option, default, **kwargs):
        option = self.__parser_option(option)
        kw = {
            "dest": option,
            "help": "(default: %s)" % default,
            "default": default
            }
        kw.update(kwargs)
        parser.add_option('', '--%s' % option, **kw)

    def inp_parser_extract(self, opts, option):
        return getattr(opts, self.__parser_option(option), None)

    def inp_metadata(self):
        return {}



class OutputParameter:
    def __init__(self):
        pass


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

    def __str__(self):
        return self.value

    @property
    def value(self):
        """The value of the string. This is either the default value
        or the parameter given on the command line"""
        return self.__value

class List(InputParameter, Type, list):
    """Can be used as: **input parameter**

    Sometimes there is the need to give a variable length of other
    **input types** as argument to an experiment. Of course here the
    command line parsing is somewhat more difficult, because the
    argument count isn't determined in before.

    The *datatype* argument is the type of the input parameter which
    should be collected::

       inputs = { "strings": List(String) }

    The default_value must be a list of compatible instances. List list
    will be used, if no arguments are given. If any argument of this
    type on the command line is given, the default_value will not be
    used::

      inputs = { "strings": List(String, default_value=[String("abc")]) }

    On the command line the List parameter can be given multiple
    times. These will be collected, if you want collect the strings
    ``["abc", "foobar", "Hallo Welt"]`` you can use the following
    parameters on the command line::

        --strings abc --strings foobar --strings "Hallo Welt"

    .. note::

       mention that the list members will appear as separate fields in
       the metadata. all start with the name of the input, and have a
       running number -%d appended.

    More complicated is the situation, when the subtype takes more
    than one command-line argument. There you can replace the name
    prefix with a colon. For example if you want to give a list of two
    :class:`~versuchung.archives.GitArchive` instances use the input
    definition ``"git": List(GitArchive)`` togehter with the command line::

       --git ":clone-url /path/to/git1" --git ":clone-url /path/to/git2"

    .. note:: Be aware of the quotation marks here!

    In the experiment the input parameter behaves like a list (it
    inherits from ``list``), so it is really easy to iterate over it::

      for string in self.inputs.strings:
          print string.value

      for git in self.inputs.git:
          # Clone all given Git Archives
          print git.path
    """

    def __init__(self, datatype, default_value=[]):
        self.__default_value = default_value
        if type(datatype) != type:
            datatype = type(datatype)
        self.datatype = datatype
        self.__command_line_parsed = False

        if hasattr(datatype, "tmp_directory"):
            self.tmp_directory = None

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, copy.deepcopy(self.__default_value), action="append",
                            help = "List parameter for type %s" %
                            self.datatype.__name__)


    def before_experiment_run(self, parameter_type):
        if parameter_type == "input" and \
                not self.__command_line_parsed:
            count = 0
            for i in self.__default_value:
                self.propagate_meta_data(count, i)
                count += 1
                self.append(i)

        for value in self:
            value.before_experiment_run(parameter_type)

    def after_experiment_run(self, parameter_type):
        for value in self:
            value.after_experiment_run(parameter_type)

    def inp_extract_cmdline_parser(self, opts, args):
        import shlex
        args = self.inp_parser_extract(opts, None)

        # No argument where given, us the default_values in before_experiment_run
        if len(args) == len(self.__default_value) and len(args) > 0\
           and type(args[0]) == type(args[0]) == self.datatype:
            return

        self.__command_line_parsed = True

        if len(args) > len(self.__default_value):
            args = [x for x in args if type(x) != self.datatype]

        count = 0
        for arg in args:
            # Create Subtype and initialize its parser
            subtype = self.datatype()
            self.propagate_meta_data(count, subtype)
            count += 1
            subtype_parser = OptionParser()
            subtype.inp_setup_cmdline_parser(subtype_parser)

            if not ":" in arg:
                arg = ": " + arg

            arg = arg.replace(": ", "--" + subtype.name + " ")
            arg = arg.replace(":", "--" + subtype.name + "-")

            arg = shlex.split(arg)

            (opts, args) = subtype_parser.parse_args(arg)
            subtype.inp_extract_cmdline_parser(opts,args)
            self.append(subtype)

    def inp_metadata(self):
        metadata = {}
        for item in self:
            metadata.update(item.inp_metadata())
        return metadata

    @property
    def value(self):
        """Returns the object (which behaves like a list) itself. This
        is only implemented for a coherent API."""
        return self

