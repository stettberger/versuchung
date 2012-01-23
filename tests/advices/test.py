#!/usr/bin/python

from versuchung.experiment import Experiment
from versuchung.files import File
from versuchung.execute import shell
import os

class SimpleExperiment(Experiment):
    def run(self):
        shell.track(self.path)
        shell("echo 1")
        shell("cd %s && test -x ./sh", "/bin")

if __name__ == "__main__":
    import shutil, sys
    experiment = SimpleExperiment()
    dirname = experiment(sys.argv)

    assert os.path.exists(dirname + "/shell_0_time")
    assert os.path.exists(dirname + "/shell_0_stdout")
    assert os.path.exists(dirname + "/shell_0_stderr")


    if dirname:
        shutil.rmtree(dirname)
    print "success"

