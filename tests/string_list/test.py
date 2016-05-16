#!/usr/bin/python3
from __future__ import print_function
import shutil

from versuchung.experiment import Experiment
from versuchung.types import List, String
from versuchung.files import File

class TestExperiment(Experiment):
    inputs = { 'stringlist' : List(String) }
    outputs = { 'result' : File("result") }

    def run(self):
        for i in self.i.stringlist:
            self.o.result.write(i.value)


if __name__ == "__main__":
    experiment = TestExperiment()

    dirname = experiment(["--stringlist", "Hello world"])
    with open("%s/result" % dirname) as fd:
        assert fd.read() == "Hello world"

    shutil.rmtree(dirname)
    print("success")
