#!/usr/bin/python

from versuchung.experiment import Experiment
from versuchung.archives import TarArchive, GitArchive

class GitArchiveTest(Experiment):
    inputs = {"git": GitArchive(TarArchive("origin.tar.gz")),
              "git_bare": GitArchive(TarArchive("origin.tar.gz"), shallow=True)
              }

    def run(self):
        directory = self.i.git.value
        assert set(["TEST", "ABC", ".git"]) == set(directory.value)

        directory = self.i.git_bare.value
        assert set(["TEST", "ABC"]) == set(directory.value)

        print "success"


if __name__ == "__main__":
    import sys
    import shutil
    t = GitArchiveTest()
    dirname = t(sys.argv)
    shutil.rmtree(dirname)
