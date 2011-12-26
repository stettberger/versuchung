#!/usr/bin/python

from versuchung.types import Type, InputParameter, Directory
from versuchung.execute import shell
import os

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
        if hasattr(self.__filename, "path"):
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

