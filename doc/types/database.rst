Database Output
***************

Similar to the :doc:`tex`, you can use a real relational database as a
backend to hold your data. Databases and tables within those databases
can be used as well as output, and as input parameters. There are
different helpers that make it easy to insert data into those
databases. When data is inserted into a database the data strictly
connected with the run experiment. This makes it at all points clear,
where data comes from and where it should go.

Please be aware, that this database interface is very very simple. If
you need some more sophisticated stuff, please use a real database
abstraction layer (e.g. with an object relation manager) like
SQLAlchemy.

The usage of the database package is straightforward. The usage of a
database table as an output is shown as an example::

  class SimpleExperiment(Experiment):
    outputs = {'table1': TableDict(),
               "table2": Table([("foo", "integer")], db = Database("foobar.db"))}

    def run(self):
        self.table1["key1"] = "value1"
        self.table1["bar"]  = "foo"

        self.table2.insert( foo = 23 )
        self.table2.insert( {"foo": 23} )

In this example two tables and two sqlite databases are created in the
output directory. The first is where table1 is located, it has the
implicit default name "sqlite3.db". The contents of the database is:

metadata table

+--------------------------------------------+--------------------------+
| experiment (text)                          |         metadata (text)  |
+============================================+==========================+
| SimpleExperiment-db3ec040e20dfc657da...    | {'experiment-version': 1,|
+--------------------------------------------+--------------------------+

SimpleExperiment__table1

+--------------------------------------------+-------------+----------------+
| experiment (text)                          | key (text)  | value (text)   |
+============================================+=============+================+
| SimpleExperiment-db3ec040e20dfc657da...    | key1        | value1         |
+--------------------------------------------+-------------+----------------+
| SimpleExperiment-db3ec040e20dfc657da...    | bar         | foo            |
+--------------------------------------------+-------------+----------------+

The ``foobar.db`` is constructed similar. But the
SimpleExperiment__table2 there has only one column of type integer.


.. automodule:: versuchung.database
   :members:

