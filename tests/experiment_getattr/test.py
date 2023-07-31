#!/usr/bin/python

from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.files import File
from versuchung.types import String
from versuchung.execute import shell
import os

class SimpleExperiment(Experiment):
    inputs = {'abc': File("/dev/null"),
              "xxx": File("/dev/null"),
              "empty": String(None)}
    outputs = {'xyz': File("asd"),
               "zzz": File("asd")}

    def run(self):
        assert self.abc == self.inputs.abc
        assert self.xyz == self.outputs.xyz
        exception = False
        try:
            self.xxx != None
        except AttributeError:
            exception = True
        assert exception == False

        assert self.empty.value is None

if __name__ == "__main__":
    import shutil, sys
    experiment = SimpleExperiment()
    dirname = experiment(sys.argv[1:])

    assert experiment.metadata["experiment-version"] == experiment.version

    if dirname:
        shutil.rmtree(dirname)
    print("success")

