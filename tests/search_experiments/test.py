#!/usr/bin/python

from versuchung.experiment import Experiment
from versuchung.types import *
from versuchung.files import *
from versuchung.files import Directory
from versuchung.execute import *
from versuchung.search import *
import sys

class Exp1(Experiment):
    inputs = {"in": String("hello")}
    outputs = {"out": CSV_File("results.csv", delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)}
    def run(self):
        pass

class Exp2(Experiment):
    inputs = {"inp": lambda self: search_experiment_results(Exp1, ".", selector=None)}
    outputs = {"out": CSV_File("results.csv", delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)}
    def run(self):
        assert len(self.inp) == 1

if __name__ == "__main__":
    import sys

    exp1 = Exp1()
    dirname1 = exp1(sys.argv)

    exp2 = Exp2()
    dirname2 = exp2(sys.argv)

    import shutil
    shutil.rmtree(dirname1)
    shutil.rmtree(dirname2)
    print("success")
