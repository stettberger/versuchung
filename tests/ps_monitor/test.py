from versuchung.experiment import Experiment
from versuchung.execute import shell, PsMonitor

class SimpleExperiment(Experiment):
    outputs = {"ps": PsMonitor("ps_monitor", tick_interval=10)}

    def run(self):
        shell = self.o.ps.shell
        shell("sleep 0.5")
        shell("seq 1 100 | while read a; do echo > /dev/null; done")
        shell("sleep 0.5")

if __name__ == "__main__":
    import shutil, sys
    try:
        import psutil
        if not "phymem_usage" in dir(psutil):
            print "skipped"
            sys.exit(0)
    except:
        print "skipped"
        sys.exit(0)

    experiment = SimpleExperiment()
    dirname = experiment(sys.argv)

    if dirname:
        shutil.rmtree(dirname)
    print "success"
