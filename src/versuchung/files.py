#!/usr/bin/python

from versuchung.types import InputParameter, OutputParameter, Type
from cStringIO import StringIO
import shutil
import csv
import os

class FilesystemObject(InputParameter, OutputParameter, Type):
    def __init__(self, default_name=""):
        self.__object_name = default_name

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__object_name)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__object_name = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.__object_name}

    @property
    def path(self):
        """:return: string -- path to the file/directory"""
        if not hasattr(self, "base_directory"):
            return os.path.abspath(self.__object_name)
        return os.path.join(self.base_directory, self.__object_name)


class File(FilesystemObject):
    """Can be used as: **input parameter** and **output parameter**

    The File type represents the content of a single file. Its
    contents can be read, overwritten and content can be appended. But
    be aware, that the content is just flushed after the experiment is
    over. If you want to do this manually use :meth:`flush`.
    """

    def __init__(self, default_filename=""):
        FilesystemObject.__init__(self, default_filename)
        self.__value = None

    @property
    def value(self):
        """This attribute can be read and written and represent the
        exact content of the specified file"""
        if not self.__value:
            try:
                with open(self.path) as fd:
                    self.__value = self.after_read(fd.read())
            except IOError:
                # File couldn't be read
                self.__value = ""
        return self.__value
    @value.setter
    def value(self, value):
        self.__value = value

    def write(self, content, append = False):
        """Similar to :attr:`value`. If append is false :attr:`value`
        is overwritten, otherwise the content is appendend"""
        if append:
            self.value += content
        else:
            self.value = content

    def outp_setup_output(self):
        # Create the file
        with open(self.path, "w+") as fd:
            fd.write("")

    def outp_tear_down_output(self):
        self.flush()

    def flush(self):
        """Flush the cached content of the file to disk"""
        with open(self.path, "w+") as fd:
            v = self.before_write(self.value)
            if v is None:
                v = ""
            fd.write(v)

    def after_read(self, value):
        """To provide filtering of file contents in subclasses, overrwrite this method.
        It is gets the file content as a string and returns the value()"""
        return value
    def before_write(self, value):
        """To provide filtering of file contents in subclasses, overrwrite this method.
        This method gets the value() and returns a string, when the file is written to disk"""
        return value

class Directory_op_with:
    def __enter__(self):
        self.olddir = os.path.abspath(os.curdir)
        os.chdir(self.path)
        return self.path
    def __exit__(self, *excinfo):
        os.chdir(self.olddir)


class Directory(FilesystemObject, Directory_op_with):
    """Can be used as: **input parameter** and **output parameter**

    Represents the contents of directory. It can also be used with the
    **with**-keyword to change the directory temporarily to this
    directory::

       with directory as dir:
          # Do something with adjusted current working directory
          print os.curdir
    """

    def __init__(self, default_filename=""):
        FilesystemObject.__init__(self, default_filename)
        self.__value = None
        self.__new_files = []

    @property
    def value(self):
        """:return: list -- directories and files in given directory"""
        if not self.__value:
            self.__value = os.listdir(self.path)
        return self.__value

    def outp_setup_output(self):
        os.mkdir(self.path)

    def outp_tear_down_output(self):
        for f in self.__new_files:
            f.outp_tear_down_output()

    def new_file(self, name):
        """Generate a new :class:`~versuchung.files.File` in the
        directory. It will be flushed automatically if the experiment
        is over."""
        f = File(name)
        f.base_directory = self.path
        self.__new_files.append(f)
        return f

    def mirror_directory(self, path):
        """Copies the contents of the given directory to this
        directory."""

        if not os.path.exists(path) and os.path.isdir(path):
            raise RuntimeError("Argument is no directory")

        for root, dirs, files in os.walk(path):
            for d in dirs:
                p = os.path.join(self.path, d)
                if not os.path.isdir(p):
                    os.mkdir(p)
            for f in files:
                src = os.path.join(path, f)
                dst = os.path.join(self.path, f)
                shutil.copyfile(src,dst)


class CSV_File(File):
    """Can be used as: **input parameter** and **output parameter**

    It is a normal :class:`~versuchung.files.File` but the content of the file is
    interpreted as a csv file. It is parsed before the value is
    exposed to the user. And formatted before the content is written
    to disk.

    Internally the :mod:`csv` is used, so all arguments to
    ``csv.reader`` and ``csv.writer`` can be given in *csv_args*."""

    value = File.value
    """Other than a normal CSV_File the value of a CSV_File is a list
    of lists, which represents the structure of the csv file. This
    value can be manipulated by the user.

    >>> CSV_File("csv_output").value
    [["1", "2", "3"]]"""

    def __init__(self, default_filename = "", **csv_args):
        File.__init__(self, default_filename)
        self.csv_args = csv_args

    def after_read(self, value):
        fd = StringIO(value)
        reader = csv.reader(fd, self.csv_args)
        return list(reader)
    def before_write(self, value):
        fd = StringIO()
        writer = csv.writer(fd, self.csv_args)
        writer.writerows(value)
        return fd.getvalue()

    def write(self):
        raise NotImplemented

    def append(self, row):
        """Append a row to the csv file

        It is just a shorthand for

        >>> csv_file.value.append([1,2,3])

        :param row: row to append
        :type row: list."""
        if type(row) != list:
            raise TypeError("list of values required")
        self.value.append(row)

