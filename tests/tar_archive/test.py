#!/usr/bin/python

from versuchung.experiment import Experiment
from versuchung.archives import TarArchive

class TarArchiveText(Experiment):
    inputs = {"tar": TarArchive("test.tar.gz")}

    def run(self):
        directory = self.i.tar.value
        assert len(directory.value) == 2
        assert "ABC" in directory.value
        assert "Hallo" in directory.value
        print "success"


if __name__ == "__main__":
    import sys
    import shutil
    t = TarArchiveText()
    dirname = t(sys.argv)
    shutil.rmtree(dirname)
