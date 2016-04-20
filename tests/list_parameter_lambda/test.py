from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types import String, List
from versuchung.files import File
from versuchung.archives import GzipFile
from versuchung.search import search_experiment_results

def find_results():
    return search_experiment_results(SimpleExperiment, ".")


class SimpleExperiment(Experiment):
    inputs = {"input_key": String("default key"),
              "input_value": String("default value")}
    outputs = {"output_file": File("output"),
               "gzip": GzipFile("foo.gz") }

    def run(self):
        # Combine the input parameters
        content = self.inputs.input_key.value \
            + ": " + self.inputs.input_value.value

        # write the result to the output file
        self.outputs.output_file.value = content + "\n"
        self.gzip.value = "BAR"

class SimpleExperiment2(Experiment):
    inputs = {"se": lambda x: List(SimpleExperiment(), default_value = find_results())}

    def run(self):
        assert type(self.se.static_experiment) == SimpleExperiment2
        assert type(self.se[0].static_experiment) == SimpleExperiment
        assert type(self.se.dynamic_experiment) == SimpleExperiment2
        assert type(self.se[0].dynamic_experiment) == SimpleExperiment2
        assert type(self.se[0].output_file.static_experiment) == SimpleExperiment
        assert type(self.se[0].output_file.dynamic_experiment) == SimpleExperiment2
        assert  self.se[0].output_file.tmp_directory.path

        for i in self.se:
            assert "abc:" in i.output_file.value
            assert i.gzip.value == "BAR"


if __name__ == "__main__":
    import shutil
    dirs_to_del = []
    experiment = SimpleExperiment()
    dirname = experiment(input_key="abc", input_value="1")
    dirs_to_del.append(dirname)

    experiment = SimpleExperiment()
    dirname = experiment(input_key="abc", input_value="2")
    dirs_to_del.append(dirname)

    experiment = SimpleExperiment2()
    dirname = experiment()
    dirs_to_del.append(dirname)

    for dirname in dirs_to_del:
        shutil.rmtree(dirname)
    print("success")
