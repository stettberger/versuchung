#!/usr/bin/python

from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.database   import Database, TableDict, Table
import os

class SimpleExperiment(Experiment):
    outputs = {'table1': TableDict(),
               'table3': TableDict(),
               "table2": Table([("foo", "integer")], db = Database(path="foobar.db"))}

    def run(self):
        self.table1["foo"] = "bar"
        self.table1["22"] = "14"
        self.table3["ABCD"] = "foo"

        keys, values = self.table1.value
        assert set(keys) == set(["key", "value"])
        self.table2.insert(foo=23)


class SimpleExperiment2(Experiment):
    inputs = {'se': SimpleExperiment()}

    def run(self):
        assert len(self.se.table1) > 0
        assert self.se.table1["foo"] == "bar"
        assert self.se.table2.value[1][0] == (23,)


if __name__ == "__main__":
    import shutil, sys
    e1 = SimpleExperiment()
    r1 = e1([])

    assert os.path.exists(os.path.join(r1, "sqlite3.db"))
    assert os.path.exists(os.path.join(r1, "foobar.db"))

    e2 = SimpleExperiment2()
    r2 = e2(se=r1)

    if r1:
        shutil.rmtree(r1)

    if r2:
        shutil.rmtree(r2)
    print("success")

