#!/usr/bin/python

from versuchung.experiment import Experiment
from versuchung.archives import TarArchive, GitArchive
import os

from multiprocessing import Pool

def do_test(git):
    pass

class GitArchiveTest(Experiment):
    inputs = {"git": GitArchive(TarArchive("origin.tar.gz")),
              "git_bare": GitArchive(TarArchive("origin.tar.gz"), shallow=True)
              }

    def run(self):
        directory = self.i.git.value
        assert set(["TEST", "ABC", ".git"]) == set(directory.value)

        directory = self.i.git_bare.value
        assert set(["TEST", "ABC"]) == set(directory.value)

        threadpool = Pool(1)
        threadpool.map(do_test, [self.git.value])

        print "success"


if __name__ == "__main__":
    import sys
    import shutil
    t = GitArchiveTest()
    dirname = t(sys.argv)
    shutil.rmtree(dirname)
