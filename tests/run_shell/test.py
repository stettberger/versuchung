from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.execute import shell, shell_failok, CommandFailed

import sys

class ShellExperiment(Experiment):
    def run(self):
        shell.track(self.path)

        shell("date")

        try:
            shell("/bin/false")
            # should always raise the exception
            assert False
        except CommandFailed:
            pass

        # this must not fail the experiment
        shell_failok("/bin/false")

        assert (['2 23'], 0) == shell("echo %(foo)s %(bar)s", {"foo": "2", "bar": "23"})

        shell("cat %s", __file__)

if __name__ == "__main__":
    import shutil
    experiment = ShellExperiment()
    dirname = experiment(sys.argv)
    print("success")
    if dirname:
        shutil.rmtree(dirname)
