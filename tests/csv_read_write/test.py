from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.files import CSV_File

class CSVExperiment(Experiment):
    inputs =  {}
    outputs = {"csv": CSV_File("csv_output")}

    def run(self):
        self.outputs.csv.value.append([1,2,3])

if __name__ == "__main__":
    import shutil, sys
    experiment = CSVExperiment()
    dirname = experiment(sys.argv)

    csv = CSV_File(dirname + "/" + "csv_output")

    assert csv.value == [["1","2","3"]]

    if dirname:
        shutil.rmtree(dirname)
    print("success")
