from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types import String
from versuchung.files import File, Directory
import os

class SimpleExperiment(Experiment):
    inputs = {"input_key": String("default key"),
              "input_value": String("default value")}
    outputs = {"output_file": File("output"),
               "output_directory": Directory("output_directory")}

    def run(self):
        # Combine the input parameters
        content = self.inputs.input_key.value \
            + ": " + self.inputs.input_value.value

        # write the result to the output file
        self.outputs.output_file.value = content + "\n"
        # New output directory
        x = self.output_directory.new_directory("foo").new_file("lala")

if __name__ == "__main__":
    import shutil, sys
    experiment = SimpleExperiment()
    dirname = experiment(sys.argv)

    assert os.path.exists("%s/output_directory/foo/lala" % dirname)

    if dirname:
        shutil.rmtree(dirname)
    print("success")
