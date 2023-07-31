#!/usr/bin/python

from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.archives import TarArchive, GitArchive
import os

class GitArchiveTest(Experiment):
    inputs = {"git":      GitArchive(TarArchive("origin.tar.gz"), tags=True, branches="master"),
              "git_full": GitArchive(TarArchive("origin.tar.gz"), tags=True, branches=True),
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

        # References and hashes
        refs = self.git.references()
        assert "refs/tags/newtag" in refs
        assert "refs/heads/newbranch" in refs

        tags = self.git.tags()
        assert "newtag" in tags
        assert len(tags) == 1

        branches = self.git.branches()
        assert set(["master", "master-2"]) == set(branches.keys())

        assert set(["master", "master-2", "newbranch"]) == set(self.git_full.branches().keys())


        self.git.checkout(tag="newtag")
        self.git.checkout(branch="master")
        try:
            x = self.git.checkout(branch="newbranch")
            assert False, "newbranch should not be visible"
        except RuntimeError as e:
            pass

        assert "git-branches" in self.metadata
        assert "master" in self.metadata["git-branches"]

        print("success")


if __name__ == "__main__":
    import shutil
    t = GitArchiveTest()
    dirname = t()

    # Reinit of Git Archive must fail
    reinit = GitArchiveTest(dirname)
    assert reinit.inputs['git'] is None
    assert reinit.inputs['git_bare'] is None


    shutil.rmtree(dirname)
