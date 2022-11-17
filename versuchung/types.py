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

from __future__ import print_function

import os
import csv
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from optparse import OptionParser
import copy
import glob

class SubObjects(dict):
    def __init__(self, type_object):
        dict.__init__(self)
        self.parent = type_object

    def __setitem__(self, key, value):
        assert not key in self or self[key] == value, "Duplicated object name: %s = %s" % (key, value)
        dict.__setitem__(self, key, value)
        value.parent_object = self.parent
        self.update()

    def update(self):
        if not "parent" in dir(self) and len(self) > 0:
            print("You probably used python multiprocessing, this might break horrible")
            return

        for name, obj in self.items():
            if self.parent.name != None:
                obj.name = "%s-%s" % (self.parent.name, name)
            else:
                obj.name = name
            obj.static_experiment  = self.parent.static_experiment
            obj.dynamic_experiment = self.parent.dynamic_experiment


class Type(object):
    static_experiment = None
    """A reference to the static enclosing experiment: where the type was defined in"""

    dynamic_experiment = None
    """A reference to the currently running experiment"""

    subobjects = None
    """A Type.Subobjects instance that collects all Types that are
       used by this type. Subordinate types"""

    parent_object = None
    """A Type instance that is the parent of this object"""

    parameter_type = None

    def __init__(self):
        # We gather a list of objects that are used by us.
        self.subobjects = SubObjects(self)
        self.__name = None

    def before_experiment_run(self, parameter_type):
        self.parameter_type = parameter_type
        self.subobjects.update()
        for subobj in self.subobjects.values():
            subobj.before_experiment_run(parameter_type)

    def after_experiment_run(self, parameter_type):
        for subobj in self.subobjects.values():
            subobj.after_experiment_run(parameter_type)

    ################################################################
    # Accessors
    ################################################################
    """This is the base type for all input and output parameters"""
    @property
    def name(self):
        return self.__name
    @name.setter
    def name(self, name):
        self.__name = name

    def path_to_root_object(self):
        """Returns all parent objects"""
        ret = []
        p = self
        while p.parent_object != None:
            ret.append(p)
            p = p.parent_object
        return list(reversed(ret))

    @property
    def value(self):
        """Default accessor for this kind of data"""
        raise NotImplemented

    @property
    def base_directory(self):
        """The base directory of a type is always the base directory
        of the (statically) enclosing experiment instance. The
        Directory has the form <ExperimentName>-<HASH>"""
        if not self.static_experiment:
            return None
        return self.static_experiment.base_directory

    @property
    def tmp_directory(self):
        """A temporary directory, which can be used during experiment
        execution. The tmp_directory is deduced through the dynamic
        experiment reference"""
        assert self.dynamic_experiment, "Type is not used part of a running experiment"
        return self.dynamic_experiment.tmp_directory

    def __repr__(self, value=None):
        if value:
            return "<%s %s '%s'>" %(self.__class__.__name__, self.__name, value)
        return "<%s %s>" %(self.__class__.__name__, self.__name)



class InputParameter:
    is_restartable = False

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

    def was_given(self):
        """Checks if an optional parameter was given"""
        if not hasattr(self, "optional_parameter_given"):
            return True
        if self.optional_parameter_given:
            return True
        return False

    def inp_parser_add(self, parser, option, default, **kwargs):
        option = self.__parser_option(option)
        kw = {
            "dest": option,
            }
        if not hasattr(self, "optional_parameter_given"):
            kw["default"] = default
            kw["help"]    = "(default: %s)" % default

        kw.update(kwargs)
        parser.add_option('', '--%s' % option, **kw)

    def inp_parser_extract(self, opts, option):
        a = getattr(opts, self.__parser_option(option), None)
        if a != None and hasattr(self, "optional_parameter_given"):
            self.optional_parameter_given = True
        return a

    def inp_metadata(self):
        return {}


def Optional(input_parameter):
    """Makes an input parameter optional. input_parameter.was_given()
    checks if the parameter was given on the command line."""
    if not isinstance(input_parameter, InputParameter):
        raise RuntimeError("Optional() can only be used with input parameters")
    input_parameter.optional_parameter_given = False
    return input_parameter


class OutputParameter:
    def __init__(self):
        pass


class String(InputParameter, Type):
    """Can be used as: **input parameter**

    A String is the most simple input parameter."""

    def __init__(self, default_value=""):
        InputParameter.__init__(self)
        Type.__init__(self)
        self.__value = default_value

    def __reinit__(self, value):
        self.__value = value

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__value)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__value = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.value}

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return Type.__repr__(self, self.__value)

    @property
    def value(self):
        """The value of the string. This is either the default value
        or the parameter given on the command line"""
        return self.__value


class Bool(InputParameter, Type):
    """Can be used as: **input parameter**

    A boolean flag parameter (will accept "yes" and "no" on the command line."""

    def __init__(self, default_value=False):
        InputParameter.__init__(self)
        Type.__init__(self)
        self.__value = default_value

    def __reinit__(self, value):
        self.__value = value

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__value)
    def inp_extract_cmdline_parser(self, opts, args):
        yes_values = ("yes", "y", "true", "1")
        no_values  = ("no", "n", "false", "0")
        self.__value = self.inp_parser_extract(opts, None)
        if type(self.value) == str and self.__value.lower() in yes_values:
            self.__value = True
        elif type(self.value) == str and self.__value.lower() in no_values:
            self.__value = False
        elif type(self.__value) == bool:
            pass
        else:
            raise RuntimeError("Wrong parameter for Bool() argument (%s = %s), possible values are %s, %s" %\
                               (self.name, self.__value, yes_values, no_values))

    def inp_metadata(self):
        return {self.name: self.value}

    def __str__(self):
        return str(self.value)

    @property
    def value(self):
        """The value of the bool. This is either the default value
        or the parameter given on the command line"""
        return self.__value

class Integer(InputParameter, Type):
    """Can be used as: **input parameter**

    A integer flag argument (will accept a number on the command line."""

    def __init__(self, default_value = 0):
        InputParameter.__init__(self)
        Type.__init__(self)
        self.__value = default_value

    def __reinit__(self, value):
        self.__value = value


    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__value)
    def inp_extract_cmdline_parser(self, opts, args):
        self.__value = self.inp_parser_extract(opts, None)
        if type(self.__value) == int:
            pass
        else:
            try:
                self.__value = int(self.__value)
            except:
                raise RuntimeError("Wrong parameter for Bool() argument (%s)" % self.__value)

    def inp_metadata(self):
        return {self.name: self.value}

    def __str__(self):
        return str(self.value)

    @property
    def value(self):
        """The value of the integer. This is either the default value
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
    definition ``"git": List(GitArchive)`` together with the command line::

       --git ":clone-url /path/to/git1" --git ":clone-url /path/to/git2"

    .. note:: Be aware of the quotation marks here!

    In the experiment the input parameter behaves like a list (it
    inherits from ``list``), so it is really easy to iterate over it::

      for string in self.inputs.strings:
          print(string.value)

      for git in self.inputs.git:
          # Clone all given Git Archives
          print(git.path)
    """

    def __init__(self, datatype, default_value=[]):
        InputParameter.__init__(self)
        Type.__init__(self)
        list.__init__(self, default_value)
        if type(datatype) != type:
            datatype = type(datatype)
        self.datatype = datatype
        self.__command_line_parsed = False

    def __reinit__(self, values):
        if hasattr(self.datatype, "__reinit__"):
            self[:] = []
            self.subobjects.clear()
            for item in values:
                # Intatiate Datatype
                item = self.datatype(item)
                self.subobjects["%d" % len(self)] = item
                self.append(item)



    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, [], action="append",
                            help = "List parameter for type %s" %
                            self.datatype.__name__)


    def before_experiment_run(self, parameter_type):
        for idx, value in enumerate(self):
            self.subobjects[str(idx)] = value

        Type.before_experiment_run(self,parameter_type)

    def inp_extract_cmdline_parser(self, opts, args):
        import shlex
        args = self.inp_parser_extract(opts, None)
        if not args:
            return

        # Remove default values
        self[:] = []
        self.subobjects.clear()

        while len(args) > 0:
            arg = args.pop(0)
            if hasattr(self.datatype, "path") and not os.path.exists(arg):
                args = glob.glob(arg) + args
                # Remove duplicated items caused by symlinks
                args = list(set([os.path.realpath(x) for x in args]))
                continue
            # Create Subtype and initialize its parser
            subtype = self.datatype()
            self.subobjects["%d" % len(self)] = subtype
            subtype_parser = OptionParser()
            subtype.inp_setup_cmdline_parser(subtype_parser)

            if not ":" in arg:
                (opts, sub_args) = subtype_parser.parse_args(["--" + subtype.name, arg])
            else:
                arg = arg.replace(": ", "--" + subtype.name + " ")
                arg = arg.replace(":", "--" + subtype.name + "-")

                arg = shlex.split(arg)
                (opts, sub_args) = subtype_parser.parse_args(arg)

            subtype.inp_extract_cmdline_parser(opts,sub_args)

            self.append(subtype)



    def inp_metadata(self):
        metadata = {self.name: []}
        for idx, item in enumerate(self):
            m = item.inp_metadata()
            metadata[self.name].append(m["%s-%d" % (self.name, idx)])
            metadata.update(m)
        return metadata

    @property
    def value(self):
        """Returns the object (which behaves like a list) itself. This
           is only implemented for a coherent API."""
        return self

    def __repr__(self):
        return Type.__repr__(self, list.__repr__(self))
