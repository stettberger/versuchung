#!/usr/bin/python
from __future__ import print_function
import sys

from versuchung.experiment import Experiment
from versuchung.types import List, String
from versuchung.files import File

class OriginalExperiment(Experiment):
    def run(self):
        pass

class TestExperiment(Experiment):
    inputs = { 'experiment' : OriginalExperiment() }

    def run(self):
        pass


if __name__ == "__main__":
    experiment = TestExperiment()

    try:
        dirname = experiment(["--experiment", "Invalid"])
    except:
        print("success")
        sys.exit(0)

    assert False
