#!/usr/bin/python

from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.files import File
from versuchung.execute import shell
import os

class SimpleExperiment(Experiment):
    def run(self):
        shell.track(self.path)
        shell("echo 1")
        shell("cd %s && test -x ./sh", "/bin")
        shell.track.disable()
        shell("echo I am silent")
        shell.track.enable()
        shell("echo Can you hear me?")

if __name__ == "__main__":
    import shutil, sys
    experiment = SimpleExperiment()
    dirname = experiment(sys.argv)

    assert os.path.exists(dirname + "/shell_0_time")
    assert os.path.exists(dirname + "/shell_0_stdout")
    assert os.path.exists(dirname + "/shell_0_stderr")
    assert os.path.exists(dirname + "/shell_1_stdout")
    assert os.path.exists(dirname + "/shell_2_stdout")
    assert not os.path.exists(dirname + "/shell_3_stdout")

    with open(dirname + "/shell_2_stdout") as fd:
        assert fd.read() == "Can you hear me?\n"

    if dirname:
        shutil.rmtree(dirname)
    print("success")

