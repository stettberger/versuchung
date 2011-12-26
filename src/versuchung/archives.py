#!/usr/bin/python

from versuchung.types import Type, InputParameter, Directory
from versuchung.execute import shell
import logging
import os
import sys

class TarArchive(Type, InputParameter):
    """Use a tar archive as input parameter. The archive will be
       extracted to the temporary directory. So it will be cleaned
       afterwards."""

    """This parameter needs an tmp_directory to extract the archive"""
    tmp_directory = None

    def __init__(self, default_filename = None):
        """The default_filename is either a string to a file. Or a
        object with a path attribute (e.g. a vamos.types.FileSystemObject)"""
        Type.__init__(self)
        self.__filename = default_filename
        self.__value = None

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__filename)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__filename = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.__filename}

    def __setup_value(self):
        fn = self.__filename
        if "path" in dir(self.__filename):
            fn = self.__filename.path

        fn = os.path.abspath(fn)

        extract_mode = ""
        if "tar.gz" in fn or "tgz" in fn:
            extract_mode = "x"
        if "tar.bz2" in fn or "bzip2" in fn:
            extract_mode = "j"

        with self.tmp_directory as d:
            os.mkdir(self.name)
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
        """Return a vamos.types.Directory instance to the extracted
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


class GitArchive(InputParameter, Type):
    """This parameter needs an tmp_directory to clone the archive"""
    tmp_directory = None

    def __init__(self, clone_url = None, ref = "refs/heads/master", shallow = False):
        """clone_url: where to the git archive from
              This might either be a string or a object with a path attribute
           ref: which git reference to checkout
           shallow: do a shallow copy (using git-archive).

           The git archive will be cloned to self.name (which is the
           key in the input parameters dict)"""
        Type.__init__(self)

        self.__clone_url = clone_url
        self.__ref = ref
        self.__shallow = shallow
        self.__value = None

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, "clone-url", self.__clone_url)
        self.inp_parser_add(parser, "ref", self.__ref)


    def inp_extract_cmdline_parser(self, opts, args):
        self.__clone_url = self.inp_parser_extract(opts, "clone-url")
        self.__ref = self.inp_parser_extract(opts, "ref")


    def inp_metadata(self):
        return {self.name + "-clone-url": str(self.__clone_url),
                self.name + "-ref": self.__ref}

    def __setup_value(self):
        if "path" in dir(self.__clone_url):
            if hasattr(self.__clone_url, "tmp_directory"):
                self.__clone_url.name = self.name + "-clone-url"
                self.__clone_url.tmp_directory = self.tmp_directory
            self.__clone_url = self.__clone_url.path

        logging.info("copying git archive %s", self.__clone_url)
        with self.tmp_directory as d:
            os.mkdir(self.name)
            if self.__shallow:
                cmd = "cd '%s' && git archive --format=tar --remote='%s' '%s' | tar x"
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
                cmd = "cd %s && git checkout %s"
                args = (self.name, self.__ref)
                (lines, ret) = shell(cmd, *args)

                if ret != 0:
                    print "\n".join(lines)
                    sys.exit(-1)


            return Directory(os.path.abspath(self.name))


    @property
    def value(self):
        """Return a vamos.types.Directory instance to the cloned git directory"""
        if not self.__value:
            self.__value = self.__setup_value()
        return self.__value
