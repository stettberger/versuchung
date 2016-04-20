from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.archives import GzipFile
from versuchung.files import Directory

class SimpleExperiment(Experiment):
    inputs = { "gz": GzipFile("content.gz") }
    outputs = {"gz_out": GzipFile("content.gz") }

    def run(self):
        with self.tmp_directory as d:
            assert self.tmp_directory.path in self.gz.path
            assert self.gz.value.strip() == "CONTENT"

            self.gz_out.value = "OUTPUT"

if __name__ == "__main__":
    import shutil, sys

    experiment = SimpleExperiment()
    dirname = experiment(sys.argv)

    assert len(open(experiment.gz_out.path).read()) > 0

    if dirname:
        shutil.rmtree(dirname)
    print("success")
