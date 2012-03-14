#!/usr/bin/python

from versuchung.types import InputParameter, OutputParameter, Type
from versuchung.tools import before
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

    The File type represents the content of a single file. Its contents
    can be read and written most easily with the :attr:`value` property.

    Alternatively, the method :meth:`write` appends new content if the
    parameter `append` is set to `True`.

    NB: The content of the file is flushed only after the experiment
    finishes.  Use :meth:`flush` to force writing the buffered data to
    disk before the experiment finishes.
    """

    def __init__(self, default_filename=""):
        FilesystemObject.__init__(self, default_filename)
        self.__value = None

    @property
    def value(self):
        """This attribute can be read and written and represent the
        content of the specified file"""
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
        """Similar to the :attr:`value` property. If the parameter
        `append` is `False`, then the property :attr:`value` is reset
        (i.e., overwritten), otherwise the content is appendend"""
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

    def copy_contents(self, filename):
        """Read the given file and replace the current .value with the
        files content.

        Flushes automatically afterwards."""
        with open(filename) as fd:
            self.value = self.after_read(fd.read())
        self.flush()

    def after_read(self, value):
        """To provide filtering of file contents in subclasses, overrwrite this method.
        It is gets the file content as a string and returns the value()"""
        return value

    def before_write(self, value):
        """To provide filtering of file contents in subclasses, overrwrite this method.
        This method gets the value() and returns a string, when the file is written to disk"""
        return value

class Directory_op_with:
    def __init__(self):
        self.__olddir = []
    def __enter__(self):
        self.__olddir.append(os.path.abspath(os.curdir))
        os.chdir(self.path)
        return self.path
    def __exit__(self, *excinfo):
        path = self.__olddir[-1]
        del self.__olddir[-1]
        os.chdir(path)


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
        Directory_op_with.__init__(self)
        self.__value = None
        self.__new_files = []

    def ___ensure_dir_exists(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    # Ensure dir exists DECORATOR
    __ensure_dir_exists = before(___ensure_dir_exists)

    @property
    def value(self):
        """:return: list -- directories and files in given directory"""
        if not self.__value:
            self.__value = os.listdir(self.path)
        return self.__value

    @__ensure_dir_exists
    def outp_setup_output(self):
        pass

    def outp_tear_down_output(self):
        for f in self.__new_files:
            f.outp_tear_down_output()

    @__ensure_dir_exists
    def new_file(self, name):
        """Generate a new :class:`~versuchung.files.File` in the
        directory. It will be flushed automatically if the experiment
        is over."""
        f = File(name)
        f.base_directory = self.path
        self.__new_files.append(f)
        return f

    @__ensure_dir_exists
    def mirror_directory(self, path, include_closure = None):
        """Copies the contents of the given directory to this
        directory.

        The include closure is a function, which checks for every
        (absolute) path in the origin directory, if it is mirrored. If
        it is None, all files are included."""

        if not include_closure:
            include_closure = lambda arg: True

        if not os.path.exists(path) and os.path.isdir(path):
            raise RuntimeError("Argument is no directory")

        path = os.path.abspath(path)

        for root, dirs, files in os.walk(path):
            root = root[len(path)+1:]
            for d in dirs:
                src = os.path.join(path, root, d)
                if not include_closure(src):
                    continue
                dst = os.path.join(self.path, root, d)
                if not os.path.isdir(dst):
                    os.mkdir(dst)
            for f in files:
                src = os.path.join(path, root, f)
                if not include_closure(src):
                    continue
                dst = os.path.join(self.path, root, f)
                shutil.copyfile(src,dst)

        self.__value = None

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

