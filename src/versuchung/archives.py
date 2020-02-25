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

from versuchung.types import Type, InputParameter
from versuchung.files import Directory, Directory_op_with, File
from versuchung.execute import shell
import logging
import os
import sys
import gzip
import re
from subprocess import PIPE
try:
    from StringIO import StringIO as BytesIO
except Exception:
    from io import BytesIO

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
            extract_mode = "z"
        if "tar.bz2" in fn or "bzip2" in fn:
            extract_mode = "j"
        if "tar.xz" in fn or "txz" in fn:
            extract_mode = "J"

        with self.tmp_directory as d:
            try:
                os.mkdir(self.name)
            except OSError:
                # ignore errors if the directory should already exist for some reason
                pass
            with Directory(self.name) as d2:
                dirname = os.path.abspath(".")
                (out, ret) = shell("tar %sxvf %s", extract_mode, fn)
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

    The git repository given in ``clone_url`` will be cloned to a
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

    def __init__(self, clone_url = None, ref = "refs/heads/master", shallow=False,
                 branches=None, tags=None):
        """clone_url: where to the git archive from
              This might either be a string or a object with a path attribute
           ref: which git reference to checkout
           shallow: do a shallow copy (using git-archive).
           branches: Also fetch other branches. Use branches=True for all branches and branches=REGEX for a filtered view.
           tags:     Also fetch other tags. Use tags=True for all tags and tags=REGEX for a filtered view.


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

        # Include branches and tags into the metadata-hash
        self.__filter_refs = {"branches": branches, "tags": tags}

        if (branches or tags ) and shallow:
             raise RuntimeError("Shallow clone and branch/tag checkout is not supported.")

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

    def __references(self, prefix_filter=None, regex_filter=None):
        (lines, ret) = shell("git ls-remote %s 'refs/*'", self.__clone_url, stderr=sys.stderr)

        if ret != 0 or lines == 0:
            print("\n".join(lines))
            raise RuntimeError("Could not list references in repository")

        ret = {}
        for line in lines:
            commit_hash, refname = line.strip().split("\t", 1)

            # Apply regex and prefix filter
            if prefix_filter:
                if not refname.startswith(prefix_filter):
                    continue
                # I have no idea where these names come from
                if refname.startswith("refs/tags/") and refname.endswith("^{}"):
                    continue
                # Shorten the Prefix
                refname = refname[len(prefix_filter):]

            if regex_filter and not re.match(regex_filter, refname):
                continue

            ret[refname] = commit_hash

        return ret

    def references(self, regex_filter=None):
        """Inspect reference list of the repository. This reference list
           includes all branches, tags, and whatsoever. All reference names are
           fully qualified (refs/tags/*, refs/heads*).

           If the ``regex_filter`` is given, only reference names that
           match the regex are returned.

           @returns a dictionary that maps references to commit hashes

        """
        return self.__references(regex_filter=regex_filter)

    def tags(self):
        """Like references, but returns a list of tags in the repository. The
           keys are transformed (refs/tags/$X -> $X).
           The GitArchive(tags=...) filter applies!


           @returns dictionary of tag name to commit hashes

        """
        regex_filter = None
        arg  = self.__filter_refs["tags"]
        if arg and arg is not True:
            regex_filter = arg
        return self.__references(prefix_filter="refs/tags/", regex_filter=regex_filter)

    def branches(self):
        """Like references, but returns a list of branches/heads in the
           repository. The keys are transformed (refs/heads/$X -> $X).
           The GitArchive(branches=...) filter applies!

           @returns dictionary of tag name to commit hashes

        """
        regex_filter = None
        arg  = self.__filter_refs["branches"]
        if arg and arg is not True:
            regex_filter = arg
        return self.__references(prefix_filter="refs/heads/", regex_filter=regex_filter)


    def checkout(self, branch=None, tag=None):
        if branch:
            visible_branches = self.__metadata.get("branches", {})
            if branch not in visible_branches:
                raise RuntimeError("Branch `%s' is not visible, please parametrize GitArchive(branches=...) correctly" % branch)
            self.__ref = "refs/heads/" + branch
            self.__hash = visible_branches[branch]
        if tag:
            visible_tags = self.__metadata.get("tags", {})
            if tag not in visible_tags:
                raise RuntimeError("Tag `%s' is not visible, please parametrize GitArchive(tags=...) correctly" % tag)
            self.__ref =  "refs/tags/" + tag
            self.__hash = visible_tags[tag]

        if not self.__ref:
            raise RuntimeError("GitArchive.checkout() requires branch or tag parameter")

        cmd = "cd '%s' && git checkout %s"
        (lines, ret) = shell(cmd, self.value.path, self.__ref, stderr=sys.stderr)
        if ret != 0:
            print("\n".join(lines))
            raise RuntimeError("GitArchive.checkout(%s) failed" % self.__ref)

        return (self.__ref, self.__hash)


    def checkout_hash(self):
        """Return the hash of the HEAD commit hash as string"""
        if not self.__hash:
            cmd = "git ls-remote %s %s" % (self.__clone_url,
                                           self.__ref)

            (lines, ret) = shell(cmd, stderr=sys.stderr)
            if ret != 0 or lines == 0:
                print("\n".join(lines))
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
        ret = {"clone-url": str(self.__clone_url),
               "ref": self.__ref,
               "hash": self.checkout_hash()}

        # If the user wants to checkout different branches, these have
        # to influence the metadata hash
        for ref, getter in [("branches", self.branches),
                            ("tags",     self.tags)]:
            if self.__filter_refs[ref]:
                ret[ref] = getter()

        self.__metadata = ret

        return {self.name + "-" + k: v for (k,v) in ret.items()}

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

            (lines, ret) = shell(cmd, *args, stderr=sys.stderr)

            if ret != 0:
                print("\n".join(lines))
                sys.exit(-1)

            if not self.__shallow:
                cmd = "cd %s && git gc && git fetch %s %s && git checkout FETCH_HEAD"
                args = (self.name, self.__clone_url, self.__ref)
                (lines, ret) = shell(cmd, *args, stderr=sys.stderr)

                if ret != 0:
                    print("\n".join(lines))
                    sys.exit(-1)

                # Fetch all visible branches and tags
                for branch in self.__metadata.get("branches", {}):
                    cmd = "cd %s && git fetch %s refs/heads/%s && git update-ref refs/heads/%s FETCH_HEAD"
                    shell(cmd, self.name, self.__clone_url, branch, branch, stderr=sys.stderr)
                for tag in self.__metadata.get("tags", {}):
                    cmd = "cd %s && git fetch %s refs/tags/%s && git update-ref refs/tags/%s FETCH_HEAD"
                    shell(cmd, self.name, self.__clone_url, tag, tag, stderr=sys.stderr)

            return Directory(os.path.abspath(self.name))

    @property
    def value(self):
        """Return a :class:`versuchung.files.Directory` instance to the cloned git directory"""
        if not self.__value:
            self.__value = self.__setup_value()
        return self.__value

    @property
    def path(self):
        """Return the string to the extract directory (same as .value.path)"""
        return self.value.path


class GzipFile(File):
    def __init__(self, default_filename=""):
        File.__init__(self, default_filename, binary=True)

    @property
    def path(self):
        """Decompress file into the temporary directory and return path to this location"""
        assert self.tmp_directory is not None, \
            "Can gunzip file only as part of an active experiment"

        path = File.path.fget(self)
        base = os.path.basename(path.rstrip(".gz"))
        filename = os.path.join(self.tmp_directory.path,
                                self.name + "_" + base)

        if not os.path.exists(filename):
            shell("gunzip < %s > %s", path, filename)

        return filename

    def after_read(self, value):
        x = BytesIO(value)
        fd = gzip.GzipFile(fileobj=x)
        return fd.read().decode()

    def before_write(self, value):
        x = BytesIO()
        fd = gzip.GzipFile(fileobj=x, mode="w")
        fd.write(value.encode())
        fd.close()
        return x.getvalue()
