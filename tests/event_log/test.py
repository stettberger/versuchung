from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.events import EventLog

class SimpleExperiment(Experiment):
    outputs = {"events": EventLog("events")}

    def run(self):
        shell = self.o.events.shell
        shell("sleep 0.5")
        shell("seq 1 100 | while read a; do echo > /dev/null; done")
        shell("sleep 0.5")

        assert len(self.o.events.value) == 9
        # Runtime of sleep 0.5 should be about half a second
        assert int(self.o.events.value[2][3] * 10) in [4,5,6]

if __name__ == "__main__":
    import shutil

    experiment = SimpleExperiment()
    dirname = experiment()

    if dirname:
        shutil.rmtree(dirname)
    print("success")
