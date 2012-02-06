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
        
if __name__ == "__main__":
    import shutil
    experiment = ShellExperiment()
    dirname = experiment(sys.argv)
    print "success"
    if dirname:
        shutil.rmtree(dirname)
