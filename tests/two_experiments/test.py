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

class SimpleExperiment2(Experiment):
    inputs = {"se": SimpleExperiment()}
    outputs = {"key": File("key") }

    def run(self):
        content = "%s: %s\n" %(self.i.se.metadata["input_key"],
                               self.i.se.metadata["input_value"])
        assert content == self.i.se.o.output_file.value
        assert self.metadata["experiment-name"] == self.title


if __name__ == "__main__":
    import shutil, sys
    e1 = SimpleExperiment()
    r1 = e1([])

    e2 = SimpleExperiment2()
    r2 = e2(se=r1)

    if r1:
        shutil.rmtree(r1)

    if r2:
        shutil.rmtree(r2)
    print "success"
