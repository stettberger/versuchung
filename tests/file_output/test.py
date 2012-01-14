from versuchung.experiment import Experiment
from versuchung.types import String
from versuchung.files import File

class SimpleExperiment(Experiment):
    inputs = {"input_key": String("default key"),
              "input_value": String("default value")}
    outputs = {"output_file": File("output")}

    def run(self):
        # Combine the input parameters
        content = self.inputs.input_key.value \
            + ": " + self.inputs.input_value.value

        # write the result to the output file
        self.outputs.output_file.value = content + "\n"


if __name__ == "__main__":
    import shutil, sys
    experiment = SimpleExperiment()
    dirname = experiment(sys.argv)

    if dirname:
        shutil.rmtree(dirname)
    print "success"
