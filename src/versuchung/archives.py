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


from versuchung.types import Type, InputParameter
from versuchung.files import Directory, Directory_op_with, File
from versuchung.execute import shell
import logging
import os
import sys

class TarArchive(Type, InputParameter, Directory_op_with):
    """Can be used as: **input parameter**

    The archive will be extracted to a temporary directory. It will be
    removed after the experiment is over.

    ``clone_url`` can either be a :class:`string` or any object that
    has a ``.path`` attribute (like
    e.g. :class:`~versuchung.filesystems.File`). Of course the
    referenced file must be a single file.

    This parameter can be used as argument to the with keyword, to
    change to the temporary directory::

        with self.inputs.tar_archive as path:
            # Here we have path == os.path.abspath(os.curdir)
            # Do something in the extracted copy
            print path
    """
    def __init__(self, filename = None):
        """The default_filename is either a string to a file. Or a
        object with a path attribute (e.g. a :class:`~versuchung.files.File`)"""
        Type.__init__(self)
        InputParameter.__init__(self)
        Directory_op_with.__init__(self)

        self.__filename = filename
        self.__value = None

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__filename)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__filename = self.inp_parser_extract(opts, None)

    def before_experiment_run(self, parameter_type):
        if parameter_type == "input" and "path" in dir(self.__filename):
            self.subobjects["filename"] = self.__filename
            Type.before_experiment_run(self, parameter_type)
            self.__filename = self.__filename.path
        else:
            Type.before_experiment_run(self, parameter_type)

        self.__filename = os.path.abspath(self.__filename)

    def inp_metadata(self):
        return {self.name: self.__filename}

    def __setup_value(self):
        if "path" in dir(self.__filename):
            self.subobjects["filename"] = self.__filename
            self.__filename = self.__filename.path

        self.__filename = os.path.abspath(self.__filename)
        fn = self.__filename

        extract_mode = ""
        if "tar.gz" in fn or "tgz" in fn:
            extract_mode = "x"
        if "tar.bz2" in fn or "bzip2" in fn:
            extract_mode = "j"

        with self.tmp_directory as d:
            try:
                os.mkdir(self.name)
            except OSError:
                # ignore errors if the directory should already exist for some reason
                pass
            with Directory(self.name) as d2:
                dirname = os.path.abspath(".")
                (out, ret) = shell("tar %szvf %s", extract_mode, fn)
                if ret != 0:
                    raise RuntimeError("Extracting of %s failed" % fn)

                cd = None
                for line in out:
                    if (cd == None or len(line) < len(cd)) and line.endswith("/"):
                        cd = line
                if cd and all([x.startswith(cd) for x in out]):
                    dirname = cd
                return Directory(os.path.abspath(dirname))

    @property
    def value(self):
        """Return a :class:`versuchung.files.Directory` instance to the extracted
        tar archive. If it contains only one directory the instance
        will point there. Otherwise it will point to a directory
        containing the contents of the archive"""
        if not self.__value:
            self.__value = self.__setup_value()
        return self.__value

    @property
    def path(self):
        """Return the string to the extract directory (same as .value.path)"""
        return self.value.path


class GitArchive(InputParameter, Type, Directory_op_with):
    """Can be used as: **input parameter**

    The in ``clone_url`` given git repository will be cloned to a
    temporary directory. It will be removed after the experiment is
    over. If ``shallow == True`` Only the files and not the .git is
    copied (cloned). This is especially useful for large git
    repositories like the Linux kernel tree.

    ``clone_url`` can either be a :class:`string` or any object that
    has a ``.path`` attribute (like e.g. :class:`TarArchive`). Of
    course the refenced path must be a directory.

    This parameter can be used as argument to the with keyword, to
    change to the temporary directory::

        with self.inputs.git_archive as path:
            # Here we have path == os.path.abspath(os.curdir)
            # Do something in the extracted copy
            print path
    """

    def __init__(self, clone_url = None, ref = "refs/heads/master", shallow = False):
        """clone_url: where to the git archive from
              This might either be a string or a object with a path attribute
           ref: which git reference to checkout
           shallow: do a shallow copy (using git-archive).

           The git archive will be cloned to self.name (which is the
           key in the input parameters dict)"""
        Type.__init__(self)
        InputParameter.__init__(self)
        Directory_op_with.__init__(self)

        self.__clone_url = clone_url
        self.__ref = ref
        self.__shallow = shallow
        self.__value = None
        self.__hash = None

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, "clone-url", self.__clone_url)
        self.inp_parser_add(parser, "ref", self.__ref)


    def inp_extract_cmdline_parser(self, opts, args):
        self.__clone_url = self.inp_parser_extract(opts, "clone-url")
        self.__ref = self.inp_parser_extract(opts, "ref")

    def before_experiment_run(self, parameter_type):
        if parameter_type == "input" and "path" in dir(self.__clone_url):
            self.subobjects["clone-url"] = self.__clone_url
            Type.before_experiment_run(self, parameter_type)
            self.__clone_url = self.__clone_url.path
        else:
            Type.before_experiment_run(self, parameter_type)

    def checkout_hash(self):
        """Return the hash of the HEAD commit hash as string"""
        if not self.__hash:
            cmd = "git ls-remote %s %s" % (self.__clone_url,
                                           self.__ref)

            (lines, ret) = shell(cmd)
            if ret != 0 or lines == 0:
                print "\n".join(lines)
                sys.exit(-1)

            self.__hash = lines[0].split("\t")[0]
            if self.__hash == "":
                self.__hash = self.__ref

        return self.__hash

    def checkout_ref(self):
        """Return git ref which was checked out"""
        return self.__ref

    def checkout_url(self):
        """Return git url which was checked out"""
        return self.__clone_url

    def inp_metadata(self):
        return {self.name + "-clone-url": str(self.__clone_url),
                self.name + "-ref": self.__ref,
                self.name + "-hash": self.checkout_hash()}

    def __setup_value(self):
        if "path" in dir(self.__clone_url):
            self.subobjects["clone-url"] = self.__clone_url
            self.__clone_url = self.__clone_url.path

        logging.info("copying git archive %s", self.__clone_url)
        with self.tmp_directory as d:
            os.mkdir(self.name)
            if self.__shallow:
                cmd = "cd '%s' && git archive --format=tar --remote=%s %s | tar x"
                args = (self.name,
                        self.__clone_url,
                        self.__ref)
            else:
                cmd = "git clone %s %s"
                args = (self.__clone_url, self.name)

            (lines, ret) = shell(cmd, *args)

            if ret != 0:
                print "\n".join(lines)
                sys.exit(-1)

            if not self.__shallow:
                cmd = "cd %s && git fetch %s %s && git checkout FETCH_HEAD"
                args = (self.name, self.__clone_url, self.__ref)
                (lines, ret) = shell(cmd, *args)

                if ret != 0:
                    print "\n".join(lines)
                    sys.exit(-1)


            return Directory(os.path.abspath(self.name))

    @property
    def value(self):
        """Return a vamos.files.Directory instance to the cloned git directory"""
        if not self.__value:
            self.__value = self.__setup_value()
        return self.__value

    @property
    def path(self):
        """Return the string to the extract directory (same as .value.path)"""
        return self.value.path


class GzipFile(File):
    def original_filename(self):
        return self.__original_filename

    @property
    def path(self):
        path = File.path.fget(self)
        if self.parameter_type == "input" and not os.path.exists(path):
            shell("gunzip < %s > %s", self.__original_filename,
                  path)
        return path

    @property
    def value(self):
        path = File.path.fget(self)
        if self.parameter_type == "input" and not os.path.exists(path):
            shell("gunzip < %s > %s", self.__original_filename,
                  path)
        return File.value.fget(self)

    @value.setter
    def value(self, value):
        File.value.fset(self, value)

    def before_experiment_run(self, parameter_type):
        self.parameter_type = parameter_type
        if parameter_type == "input":
            self.__original_filename = File.path.fget(self)
            self.subobjects["filename"] = File(self.__original_filename)
            filename = self.name + "_" + os.path.basename(self.path.rstrip(".gz"))
            self.set_path(self.tmp_directory.path, filename)

        File.before_experiment_run(self, parameter_type)

    def after_experiment_run(self, parameter_type):
        File.after_experiment_run(self, parameter_type)
        if parameter_type == "output":
            shell("gzip -c %s > %s.1", self.path, self.path)
            shell("mv %s.1 %s", self.path, self.path)

