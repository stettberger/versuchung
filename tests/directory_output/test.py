from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types import String
from versuchung.files import Directory, File
from versuchung.archives import GzipFile
import os

class SimpleExperiment(Experiment):
    outputs = {"dir1": Directory("d1"),
               "dir2": Directory("d2"),
               "filtered": Directory(".", filename_filter="*.log*"),
              }

    def run(self):
        a = self.o.dir1.new_file("barfoo")
        a.value="abc"
        a.flush()
        os.mkdir(self.o.dir1.path + "/tmpdir")
        with open(self.o.dir1.path + "/tmpdir/foo", "w+") as fd:
            fd.write("Hallo")

        self.o.dir2.mirror_directory(self.o.dir1.path,
                                     lambda x: True)

        a = self.filtered.new_file("foo.log")
        a.value = "xx"
        try:
            a = self.filtered.new_file("bar.xxx")
            raise Exception("Filter does not work")
        except RuntimeError as e:
            pass # Everything is good

        b = self.filtered.new_file("barfoo.log.gz", compressed=True)
        b.value = "xx"

        assert type(a) == File
        assert type(b) == GzipFile



if __name__ == "__main__":
    import shutil, os
    experiment = SimpleExperiment()
    dirname = experiment([])

    assert os.path.isdir(experiment.o.dir2.path + "/tmpdir")
    assert os.path.exists(experiment.o.dir2.path + "/barfoo")
    assert os.path.exists(experiment.o.dir2.path + "/tmpdir/foo")

    N = Directory(experiment.path, "*.log*")
    assert experiment.filtered.value == N.value
    assert os.path.exists(experiment.path + "/foo.log")

    contents = [x.value for x in N]
    assert len(contents) == 2
    assert contents[0] == contents[1], contents

    if dirname:
        shutil.rmtree(dirname)
    print("success")
