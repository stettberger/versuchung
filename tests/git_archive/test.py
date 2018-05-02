#!/usr/bin/python

from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.archives import TarArchive, GitArchive
import os

class GitArchiveTest(Experiment):
    inputs = {"git":      GitArchive(TarArchive("origin.tar.gz")),
              "git_bare": GitArchive(TarArchive("origin.tar.gz"), shallow=True)
              }

    def run(self):
        directory = self.i.git.value
        assert set(["TEST", "ABC", ".git"]) == set(directory.value)

        directory = self.i.git_bare.value
        assert set(["TEST", "ABC"]) == set(directory.value)

        with self.i.git as path:
            assert path == self.i.git.value.path
            assert os.path.abspath(os.curdir) == path

        print("success")


if __name__ == "__main__":
    import sys
    import shutil
    t = GitArchiveTest()
    dirname = t(sys.argv)

    # Reinit of Git Archive must fail
    reinit = GitArchiveTest(dirname)
    assert reinit.inputs['git'] is None
    assert reinit.inputs['git_bare'] is None


    shutil.rmtree(dirname)
