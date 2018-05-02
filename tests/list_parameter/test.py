from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types import String, List

class SimpleExperiment(Experiment):
    inputs = {"strings": List(String(), default_value=[]),
              "default": List(String, default_value=[String("foo")]),
              "default2": List(String, default_value=[String("fox")]),
              "default3": List(String, default_value=[String("a"), String("b")])
    }


    def run(self):
        strings = [s.value for s in self.i.strings]
        assert  strings == ["x86", "sparc"]

        default = [s.value for s in self.i.default]
        assert  default == ["foo"]

        default2 = [s.value for s in self.i.default2]
        assert  default2 == ["bar"]

        assert self.metadata["strings-0"] == "x86"
        assert self.metadata["strings-1"] == "sparc"

if __name__ == "__main__":
    import shutil
    experiment = SimpleExperiment()
    strings = ["--strings", "x86", "--strings", "sparc", "--default2", "bar"]
    dirname = experiment(strings)

    if dirname:
        shutil.rmtree(dirname)
    print("success")
