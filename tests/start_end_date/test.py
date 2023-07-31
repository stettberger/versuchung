from __future__ import print_function

from versuchung.experiment import Experiment
import time
class SimpleExperiment(Experiment):
    def run(self):
        time.sleep(0.1)

if __name__ == "__main__":
    import shutil, sys, os
    experiment = SimpleExperiment()
    dirname = experiment(sys.argv[1:])

    assert experiment.metadata["date-start"] != experiment.metadata["date-end"]

    if dirname:
        shutil.rmtree(dirname)
    print("success")
