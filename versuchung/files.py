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


from versuchung.types import InputParameter, OutputParameter, Type
import versuchung.archives
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import shutil
import csv
import os, stat
import hashlib
import fnmatch

class FilesystemObject(InputParameter, OutputParameter, Type):
    def __init__(self, default_name=""):
        InputParameter.__init__(self)
        OutputParameter.__init__(self)
        Type.__init__(self)
        self.__object_name = default_name
        self.__enclosing_directory = os.path.abspath(os.curdir)
        self.__force_enclosing_directory = False

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__object_name)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__object_name = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.__object_name}

    @property
    def path(self):
        """:return: string -- path to the file/directory"""
        if not self.__force_enclosing_directory:
            if self.parameter_type == "input":
                if self.static_experiment == self.dynamic_experiment:
                    self.__enclosing_directory = self.dynamic_experiment.startup_directory
                else:
                    self.__enclosing_directory = self.static_experiment.base_directory
            elif self.parameter_type == "output":
                assert self.static_experiment == self.dynamic_experiment
                self.__enclosing_directory = self.dynamic_experiment.base_directory
            elif self.static_experiment is not None:
                self.__enclosing_directory = self.static_experiment.base_directory
            else:
                self.__enclosing_directory = os.path.abspath(os.curdir)

        if os.path.isabs(self.__object_name):
            return self.__object_name

        return os.path.join(self.__enclosing_directory, self.__object_name)

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def dirname(self):
        return os.path.dirname(self.path)

    def set_path(self, base_directory, object_name):
        assert base_directory[0] == "/"
        self.__force_enclosing_directory = True
        self.__enclosing_directory = base_directory
        self.__object_name         = object_name

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

    def __init__(self, default_filename="", binary=False):
        FilesystemObject.__init__(self, default_filename)
        self.__value = None

        self.__binary = binary
        if binary:
            self.__binary_mode = "b"
        else:
            self.__binary_mode = ""


    @property
    def value(self):
        """This attribute can be read and written and represent the
        content of the specified file"""
        if not self.__value:
            try:
                with open(self.original_path, "r" + self.__binary_mode) as fd:
                    self.__value = self.after_read(fd.read())
            except IOError:
                # File couldn't be read
                self.__value = self.after_read("")
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    @property
    def original_path(self):
        return File.path.fget(self)

    def write(self, content, append = False):
        """Similar to the :attr:`value` property. If the parameter
        `append` is `False`, then the property :attr:`value` is reset
        (i.e., overwritten), otherwise the content is appendend"""
        if append:
            self.value += content
        else:
            self.value = content

    def after_experiment_run(self, parameter_type):
        FilesystemObject.after_experiment_run(self, parameter_type)
        assert parameter_type in ["input", "output"]
        if parameter_type == "output":
            self.flush()

    def flush(self):
        """Flush the cached content of the file to disk"""
        if self.__value == None:
            return
        with open(self.original_path, "w" + self.__binary_mode + "+") as fd:
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

    def make_executable(self):
        """makes a file exectuable (chmod +x $file)"""
        st = os.stat(self.original_path)
        os.chmod(self.original_path, st.st_mode | stat.S_IEXEC)

    def after_read(self, value):
        """To provide filtering of file contents in subclasses, overrwrite this method.
        It is gets the file content as a string and returns the value()"""
        return value

    def before_write(self, value):
        """To provide filtering of file contents in subclasses, overrwrite this method.
        This method gets the value() and returns a string, when the file is written to disk"""
        return value

class Executable(File):
    """Can be used as: **input parameter**

    An executable is a :class:`versuchung.files.File` that only
    references an executable. It checksums the executable and puts the
    checksum into the metadata. The executable is never changed.

    """
    def __init__(self, default_filename):
        File.__init__(self, default_filename)

    @property
    def value(self):
        raise NotImplemented

    @value.setter
    def value(self, value):
        raise NotImplementedError

    def write(self, content, append = False):
        raise NotImplementedError

    def after_experiment_run(self, parameter_type):
        pass

    def flush(self):
        raise NotImplementedError

    def copy_contents(self, filename):
        raise NotImplementedError

    def make_executable(self):
        raise NotImplementedError

    def inp_metadata(self):
        return {self.name + "-md5": hashlib.md5(open(self.path, "rb").read()).hexdigest()}

    def execute(self, cmdline, *args):
        """Does start the executable with meth:`versuchung.execute.shell` and
        args, which is of type list, as arguments."""
        from versuchung.execute import shell

        shell(self.path + " " + cmdline, *args)

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

    Represents the contents of directory. The filename_filter is a
    glob/fnmatch expression to filter the directories content and to
    ensure that no file is generated that does not fit this pattern.
    An useful example of this is an output Directory that matches only
    *.log files and is directly located in the result directory:

       outputs = {
           "logs": Directory(".", filename_filter="*.log")
       }

    It can also be used with the **with**-keyword to change the
    current working directory temporarily to this directory::

       with directory as dir:
          # Do something with adjusted current working directory
          print os.curdir

    """

    def __init__(self, default_filename="", filename_filter="*"):
        FilesystemObject.__init__(self, default_filename)
        Directory_op_with.__init__(self)
        self.filename_filter = filename_filter
        self.__value = None
        self.__new_files = []

    def __ensure_dir_exists(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    @property
    def value(self):
        """:return: list -- directories and files in given directory"""
        if not self.__value:
            self.__value = os.listdir(self.path)
            self.__value = [x for x in self.__value
                            if fnmatch.fnmatch(x, self.filename_filter)]
        return self.__value

    def __iter__(self):
        for name in self.value:
            p = os.path.join(self.path, name)
            if name in self.subobjects:
                yield self.subobjects[name]
                continue

            if os.path.isdir(p):
                d = Directory(name)
                d.set_path(self.path, p)
                self.subobjects[name] = d
                yield d
            else:
                if p.endswith(".gz"):
                    f = versuchung.archives.GzipFile(name)
                else:
                    f = File(name)
                f.set_path(self.path, p)
                self.subobjects[name] = f
                yield f

    def before_experiment_run(self, parameter_type):
        FilesystemObject.before_experiment_run(self, parameter_type)
        if parameter_type == "output":
            self.__ensure_dir_exists()

    def new_file(self, name, compressed=False):
        """Generate a new :class:`~versuchung.files.File` in the
        directory. It will be flushed automatically if the experiment
        is over."""
        if not fnmatch.fnmatch(name, self.filename_filter):
            raise RuntimeError("Filename {} does not match filter {}".\
                                 format(name, self.filename_filter))
        self.__ensure_dir_exists()
        if compressed:
            f = versuchung.archives.GzipFile(name)
        else:
            f = File(name)
        f.set_path(self.path, name)
        f.value = ""
        self.subobjects[name] = f
        return f

    def new_directory(self, name):
        """Generate a new :class:`~versuchung.files.Directory` in the
        directory. The directory <name> must not be present before"""
        if not fnmatch.fnmatch(name, self.filename_filter):
            raise RuntimeError("Filename {} does not match filter {}".\
                                 format(name, self.filename_filter))
        self.__ensure_dir_exists()
        f = Directory(name)
        f.set_path(self.path, name)
        os.mkdir(f.path)
        self.subobjects[name] = f
        return f


    def mirror_directory(self, path, include_closure = None):
        """Copies the contents of the given directory to this
        directory.

        The include closure is a function, which checks for every
        (absolute) path in the origin directory, if it is mirrored. If
        it is None, all files are included."""

        self.__ensure_dir_exists()

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
