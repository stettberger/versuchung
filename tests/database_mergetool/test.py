#!/usr/bin/python

from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types      import Integer
from versuchung.database   import Database, TableDict, Table, Database_SQlite_Merger
import os

class DatabaseGenerator(Experiment):
    inputs  = {'mode': Integer(0) }
    outputs = {'keydict': TableDict(),
               "table2": Table([("version", "integer"),
                                ("method", "text"),
                                ("result", "text")],
                               keys = ["version", "method"],
                               conflict_strategy = "REPLACE")}

    def run(self):
        for i in range(0, self.mode.value + 3):
            self.keydict[str(i)] = "barfoo " + str(i)

        if self.mode.value == 0:
            self.table2.insert(version = 1, method = "GET", result = "404") # 1
            self.table2.insert(version = 1, method = "GET", result = "404") # 2: replace 1
            self.table2.insert(version = 1, method = "POST", result = "200")# 3
        else:
            self.table2.insert(version = 1, method = "GET", result = "200") # 4: replace 2
            self.table2.insert(version = 1, method = "GET", result = "300") # 5: replace 4
            self.table2.insert(version = 1, method = "DROP", result = "404") # 6
            self.table2.insert(version = 1, method = "POST", result = "200") # 7: replace 3

        # After merging are in Database 7, 6, 5

if __name__ == "__main__":
    import shutil, sys
    e1 = DatabaseGenerator()
    r1 = e1(["--mode=0"])

    e2 = DatabaseGenerator()
    r2 = e2(["--mode=10"])


    merger = Database_SQlite_Merger("output.db", [e1.table2.database.path],
                                    logging = False)
    merger.merge()

    merger = Database_SQlite_Merger("output.db", [e2.table2.database.path],
                                    logging = False)
    merger.merge(update = True)

    merger = Database_SQlite_Merger("output.db", [e2.table2.database.path],
                                    logging = False)
    merger.merge(update = True)


    # Test the resulting database
    import sqlite3
    conn = sqlite3.connect("output.db")

    cur = conn.cursor()

    # Checking table 2
    cur.execute("SELECT * from DatabaseGenerator__table2")
    table2 = cur.fetchall()
    assert len(table2) == 3
    assert all([x[0] == table2[0][0] for x in table2])
    table2 = set([x[1:] for x in table2])
    assert (1, "POST", "200") in table2
    assert (1, "DROP", "404") in table2
    assert (1, "GET",  "300") in table2

    # Checking Metadata
    cur.execute("SELECT * from metadata")
    metadata = cur.fetchall()
    metadata = dict([(x[0], eval(x[1])) for x in metadata])
    assert metadata[e1.experiment_identifier]["mode"] == 0
    assert metadata[e2.experiment_identifier]["mode"] == 10

    # Checking Keydict
    cur.execute("SELECT * from DatabaseGenerator__keydict")
    keydict = cur.fetchall()
    keydict = dict([(x[1], x[2]) for x in keydict])
    assert len(keydict) == 13
    assert keydict['10'] == 'barfoo 10'

    cur.close()

    conn.close()


    if r1:
        shutil.rmtree(r1)

    if r2:
        shutil.rmtree(r2)

    os.unlink("output.db")

    print("success")

