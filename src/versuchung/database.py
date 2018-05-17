# This file is part of versuchung.
#
# versuchung is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# versuchung is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# versuchung.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

from versuchung.types import Type, InputParameter, OutputParameter
import logging
import sqlite3
import os, stat

# Import mysql handler
try:
    import MySQLdb
    import _mysql_exceptions
except:
    pass


class Database_Abstract:
    def values(self, table_name, filter_expr = "where experiment = ?", *args):
        """Get the contets of a table in the database. It takes
        addtional to the table name, a filter expression and applies
        all args to the excute command. An example::

           (cols, rows) = database.values("metadata", "")
           for row in rows:
                print cols, rows
        """
        cur = self.handle.cursor()
        cur.execute('select * from ' + table_name + filter_expr,
                    args)

        cols = [x[0] for x in cur.description]
        def generator():
            while True:
                row = cur.fetchone()
                if row == None:
                    cur.close()
                    return
                yield row

        index = cols.index("experiment")
        return cols, generator()

class Database_MySQL(InputParameter, OutputParameter, Type, Database_Abstract):
    """Can be used as **input parameter** and **output parameter**

    A database backend class for a MySQL database."""

    def __init__(self, database = None, host = "localhost", user = None, password = None):
        InputParameter.__init__(self)
        OutputParameter.__init__(self)
        Type.__init__(self)

        assert database != None, "Please give a database name to database connection"

        self.__database_name = database
        self.__database_host = os.environ.get("MYSQL_HOST", None) or host
        self.__database_user = os.environ.get("MYSQL_USER", None) or user
        self.__database_password = os.environ.get("MYSQL_PASSWORD", None) or password
        self.__database_connection = None

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, "database", self.__database_name)
        self.inp_parser_add(parser, "host", self.__database_host)
        self.inp_parser_add(parser, "user", self.__database_user)
        self.inp_parser_add(parser, "password", self.__database_password)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__database_name = self.inp_parser_extract(opts, "database")
        self.__database_host = self.inp_parser_extract(opts, "host")
        self.__database_user = self.inp_parser_extract(opts, "user")
        self.__database_password = self.inp_parser_extract(opts, "password")


    def inp_metadata(self):
        return {self.name + "-database": self.__database_name,
                self.name + "-host": self.__database_host}

    def install_my_cnf(self):
        """Creates a my.cnf file and sets the environment variable MYSQL_HOME"""
        directory = self.tmp_directory.new_directory(self.name)
        path = os.path.join(directory.path, "my.cnf")
        logging.debug("MYSQL_HOME=%s", path)
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT, 0o600), 'w') as handle:
            handle.write("""[client]
host=%s
user=%s
password=%s
database=%s
""" %(self.__database_host, self.__database_user, self.__database_password, self.__database_name))

        # Set the environment variable to the directory the my.cnf is located
        os.environ["MYSQL_HOME"] = directory.path

        if os.path.exists(os.path.join(os.environ["HOME"], ".my.cnf")):
            logging.warning("~/.my.cnf does overwrite versuchung's file")

    def before_experiment_run(self, parameter_type):
        Type.before_experiment_run(self, parameter_type)
        assert parameter_type in ["input", "output"]

        args = {"db": self.__database_name,
                "host": self.__database_host}
        if self.__database_user:
            args["user"] = self.__database_user
        if self.__database_password:
            args["passwd"] = self.__database_password

        default_file = os.path.join(os.environ["HOME"], ".my.cnf")
        if os.path.exists(default_file):
            args["read_default_file"] = default_file

        self.__database_connection = MySQLdb.connect(**args)

        if parameter_type == "output":
            try:
                self.create_table("metadata", [("experiment", "varchar(256)"), ("metadata", "text")],
                                  keys = ["experiment"],
                                  conflict_strategy = "REPLACE")
            except _mysql_exceptions.OperationalError as e:
                # Metadata table was already generated
                pass

            self.execute("REPLACE INTO metadata(experiment, metadata) values(?, ?)",
                         self.dynamic_experiment.experiment_identifier,
                         str(self.dynamic_experiment.metadata))

    @property
    def handle(self):
        """:return: handle -- MySQLdb database handle"""
        assert self.__database_connection
        return self.__database_connection

    def execute(self, command, *args):
        """Execute command including the arguments on the sql
        handle. Question marks in the command are replaces by the ``*args``::

        >>> database.execute("SELECT * FROM metadata WHERE experiment = ?", identifer)
        """
        logging.debug("mysql: %s %s", str(command), str(args))
        c = self.__database_connection.cursor()
        c.execute(command.replace("?", "%s"), args)
        self.__database_connection.commit()
        return c

    def create_table(self, name, fields = [("key", "text"), ("value", "text")],
                     keys = None, conflict_strategy = None):
        """Creates a new table in the database. ``name`` is the name
        of newly created table. The ``fields`` are a list of
        columns. A column is a tuple, its first entry is the name, its
        second entry the column type. If primary is the name of a
        column this column is marked as the primary key for the
        table.

        conflict_strategy is ignored!
        """

        CT = "CREATE TABLE " + name + " ("
        CT += ", ".join([ "%s %s" % x for x in fields])
        if keys:
            assert set(keys).issubset(set([x[0] for x in fields]))
            CT += ", UNIQUE(" + (", ".join(keys)) + ")"
        CT += ")"

        return self.execute(CT)


class Database_SQLite(InputParameter, OutputParameter, Type, Database_Abstract):
    """Can be used as **input parameter** and **output parameter**

    A database backend class for sqlite3 database."""

    # Static cache of all database connections open in system
    # Map from path -> tuple(db_handle, use_count)
    database_connections = {}

    def __init__(self, path = "sqlite3.db"):
        InputParameter.__init__(self)
        OutputParameter.__init__(self)
        Type.__init__(self)

        self.__database_path = path
        self.__database_connection = None

    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__database_path)

    def inp_extract_cmdline_parser(self, opts, args):
        self.__database_path = self.inp_parser_extract(opts, None)

    def inp_metadata(self):
        return {self.name: self.__database_path}

    def before_experiment_run(self, parameter_type):
        Type.before_experiment_run(self, parameter_type)
        assert parameter_type in ["input", "output"]
        if parameter_type == "input":
            # Ensure the path does exist
            if not os.path.exists(self.path):
                raise RuntimeError("Database not found: %s" % self.path)
        self.__database_connection = self.__connect(self.path)

        if parameter_type == "output":
            try:
                self.create_table("metadata", [("experiment", "text"), ("metadata", "text")],
                                  keys = ["experiment"],
                                  conflict_strategy = "REPLACE")
            except sqlite3.OperationalError as e:
                # Metadata table was already generated
                pass

            self.execute("INSERT INTO metadata(experiment, metadata) values(?, ?)",
                         self.dynamic_experiment.experiment_identifier,
                         str(self.dynamic_experiment.metadata))



    def after_experiment_run(self, parameter_type):
        Type.before_experiment_run(self, parameter_type)
        assert parameter_type in ["input", "output"]
        self.__database_connection = None
        self.__disconnect(self.path)
        if parameter_type == "output":
            # Remove execute and write permissions for file
            new_mode = os.stat(self.path).st_mode & (stat.S_IROTH | stat.S_IRGRP | stat.S_IRUSR)
            os.chmod(self.path, new_mode)

    @staticmethod
    def __connect(path):
        # Do reference counting on database connections
        if path in Database_SQLite.database_connections:
            (db, count) = Database_SQLite.database_connections[path]
            Database_SQLite.database_connections[path] = (db, count + 1)
            return db
        conn = sqlite3.connect(path)
        Database_SQLite.database_connections[path] = (conn, 1)
        return conn

    @staticmethod
    def __disconnect(path):
        (db, count) = Database_SQLite.database_connections[path]
        db.commit()
        if count == 1:
            db.close()
            del Database_SQLite.database_connections[path]
            return
        Database_SQLite.database_connections[path] = (db, count - 1)

    @property
    def path(self):
        """:return: string -- path to the sqlite database file"""
        return os.path.join(self.base_directory, self.__database_path)

    @property
    def handle(self):
        """:return: handle -- sqlite3 database handle"""
        assert self.__database_connection
        return self.__database_connection

    def execute(self, command, *args):
        """Execute command including the arguments on the sql
        handle. Question marks in the command are replaces by the ``*args``::

        >>> database.execute("SELECT * FROM metadata WHERE experiment = ?", identifer)
        """
        logging.debug("sqlite: %s %s", str(command), str(args))
        return self.__database_connection.execute(command, args)



    def create_table(self, name, fields = [("key", "text"), ("value", "text")],
                     keys = None, conflict_strategy = "REPLACE"):
        """Creates a new table in the database. ``name`` is the name
        of newly created table. The ``fields`` are a list of
        columns. A column is a tuple, its first entry is the name, its
        second entry the column type. If primary is the name of a
        column this column is marked as the primary key for the
        table."""

        CT = "CREATE TABLE " + name + " ("
        CT += ", ".join([ "%s %s" % x for x in fields])
        if keys:
            assert set(keys).issubset(set([x[0] for x in fields]))
            CT += ", UNIQUE(" + (", ".join(keys)) + ")"
            CT += " ON CONFLICT "  + conflict_strategy
        CT += ")"

        return self.execute(CT)



def Database( database_type = "sqlite", *args, **kwargs):
    """This is a just a wrapper around the supported database
    abstraction classes. Every other argument and paramater than
    ``database_type`` is forwared directly to those classes.

    Supported database_type abstractions are at the moment:

    - ``sqlite`` -- :class:`~versuchung.database.Database_SQLite`
    - ``mysql`` -- :class:`~versuchung.database.Database_MySQL`
    """
    if database_type == "sqlite":
        if not "path" in kwargs:
            kwargs["path"] = "sqlite3.db"
        return Database_SQLite(*args, **kwargs)
    if database_type == "mysql":
        return Database_MySQL(*args, **kwargs)
    assert False, "Database type %s is not implemented yet" % database_type

class Table(InputParameter, OutputParameter, Type):
    """Can be used as **input parameter** and **output parameter**

    A versuchung table is a table that is aware of experiments. It
    stores for each dataset the experiment it originates from. The
    field list consists either of plain strings, then the column type
    is text. If it's a tuple the first entry is the name and the second its type::

    >>> [("foo", "integer"), "barfoo"]

    This will result in two columns, one with type integer and one
    with type text. If a db is given this one is used instead of a
    default sqlite database named ``sqlite3.db``

    To make a set of field the index keys (UNIQUE), give it as a list
    of string as keys argument. The conflict_strategy gives the SQL
    strategy what to do on conflict. If you want to merge databases from
    multiple experiments without triggering a conflict if the given key
    set is equal (i.e., if you want the same values in the columns given
    as keys to be treated different when coming from different
    experiments), add ``experiment`` to the key set.
    """
    def __init__(self, fields, keys = None, db = None, conflict_strategy = "FAIL" ):
        self.read_only = True
        InputParameter.__init__(self)
        OutputParameter.__init__(self)
        Type.__init__(self)

        self.__keys = keys
        self.__fields = self.__field_typify(["experiment"] + fields)
        self.__conflict_strategy = conflict_strategy

        if not db:
            self.__db = Database()
        else:
            self.__db = db

    def __field_typify(self, fields):
        real_fields = []
        for f in fields:
            if type(f) in [tuple, list]:
                real_fields.append(tuple(f))
            else:
                # the default field type is text
                assert type(f) == str
                real_fields.append(tuple([f, 'text']))
        return real_fields

    def before_experiment_run(self, parameter_type):
        # Add database object as an
        self.subobjects["database"] = self.__db
        Type.before_experiment_run(self, parameter_type)

        if parameter_type == "output":
            self.read_only = False
            self.__db.create_table(self.table_name, self.__fields,
                                   keys = self.__keys,
                                   conflict_strategy = self.__conflict_strategy)
    @property
    def database(self):
        """:return: :class:`~versuchung.database.Database` -- the database the table is located in"""
        return self.__db

    @property
    def table_name(self):
        """:return: string -- return the name of the table in the database"""
        assert self.static_experiment
        name = self.name
        try:
            i = self.name.rindex("-")
            name = name[i+1:]
        except:
            pass
        return self.static_experiment.title + "__" + name

    def insert(self, data=None, **kwargs):
        """Insert a dict of data into the database table"""
        assert self.read_only == False
        if data:
            kwargs.update(data)
        kwargs["experiment"] = self.dynamic_experiment.experiment_identifier
        assert set(kwargs.keys()) == set([f for f, t in self.__fields])

        items = kwargs.items()
        insert_statement = "INSERT INTO %s(%s) values(%s)" % (
            self.table_name,
            ", ".join([f for f, t in items]),
            ", ".join(["?" for _ in items]))
        self.__db.execute(insert_statement, *[v for k,v in items])

    def clear(self):
        """Remove all entries associated with the current running experiment"""

        self.__db.execute("DELETE FROM " + self.table_name +" WHERE experiment = ?",
                          self.dynamic_experiment.experiment_identifier)

    @property
    def value(self):
        """The value of the table. It returns a tuple. The first entry
        is a tuple of column headings. The second entry is a list of
        rows, in the same order as the column headings. The column
        that associates the entry with the experiment is stripped
        apart and only data for the static enclosing experiment is
        shown."""
        (cols, rows) = self.__db.values(self.table_name, ' where experiment = ?',
                                        self.static_experiment.experiment_identifier)

        index = cols.index("experiment")
        table = []
        for row in rows:
            l = list(row)
            del l[index]
            table.append(tuple(l))
        del cols[index]

        return tuple(cols), table


class TableDict(Table, dict):
    """Can be used as **input parameter** and **output parameter**

    This uses a :class:`~versuchung.database.Table` as a backend for a
    python dict. This object can be used in the same way
    :class:`~versuchung.tex.PgfKeyDict` is used. Please be aware, that
    the storage and retrieval of keys from the associated table is
    done lazy. Therefore the data is only then visible if the
    experiment was successful.
    """
    def __init__(self, db=None):
        self.__key_name = "key"
        self.__value_name = "value"
        columns = [(self.__key_name, 'text'), (self.__value_name, 'text')]
        Table.__init__(self, columns, keys=[self.__key_name], db=db,
                       conflict_strategy = "REPLACE")
        dict.__init__(self)

    def insert(self, *args, **kwargs):
        raise NotImplementedError

    def flush(self):
        """Save the current dict content to the database."""
        Table.clear(self)
        for key, value in self.items():
            Table.insert(self,
                         {self.__key_name: key,
                          self.__value_name: value})

    def after_experiment_run(self, parameter_type):
        assert self.parameter_type == parameter_type
        if parameter_type == "output":
            self.flush()
        Table.after_experiment_run(self, parameter_type)

    def before_experiment_run(self, parameter_type):
        Table.before_experiment_run(self, parameter_type)
        if parameter_type == "input":
            (header, values) = self.value
            key_index = header.index(self.__key_name)
            value_index = header.index(self.__value_name)
            self.update([(x[key_index], x[value_index]) for x in values])



class Database_SQlite_Merger:
    def log(self, msg, *args):
        if self.logging:
            print("merger: " + (msg % args))

    def __init__(self, target_path, source_paths = [], logging = True):
        self.target_path = target_path
        self.logging = logging
        self.source_paths = {}
        self.target = sqlite3.connect(target_path)

        db_counter = 0
        for source in source_paths:
            assert os.path.exists(source), "Path does not exist " + source
            name = "db_%d" % db_counter
            db_counter += 1
            self.target.execute("ATTACH DATABASE '%s' AS %s" %(source, name))
            self.log("attached %s as %s", source, name)
            self.source_paths[name] = source

    def collect_and_create_tables(self, drop = True):
        cur = self.target.cursor()
        self.tables = {}
        for db in self.source_paths:
            cur.execute("SELECT * FROM " + db + ".sqlite_master WHERE type = 'table'")
            header = [x[0] for x in cur.description]
            for table in cur.fetchall():
                table = dict(zip(header, table))
                name = table["name"]
                if table["name"] in self.tables:
                    if self.tables[name]["sql"] != table["sql"]:
                        self.log("Two tables with different defintions found: %s" % name)
                        sys.exit(-1)
                    self.tables[name]["databases"].append(db)
                else:
                    self.tables[name] = table
                    self.tables[name]["databases"] = [db]
        for name, table in self.tables.items():
            if drop:
                try:
                    cur.execute("DROP TABLE %s" % name)
                except:
                    pass
                cur.execute(table["sql"])
            else:
                cur.execute(table["sql"].replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS'))

            self.log("created table %s", name)

        cur.close()

    def collect_data(self):
        cur = self.target.cursor()

        TableDictrows = set()

        for name in self.tables:
            rows = set()
            headers = None
            for db in self.tables[name]["databases"]:
                cur.execute("SELECT * FROM %s.%s" % (db, name))
                for i in cur.fetchall():
                    rows.add(i)
                headers = [x[0] for x in cur.description]

            cur.executemany("INSERT INTO %s (%s) values(%s)" % (\
                    name,
                    ", ".join(headers),
                    ", ".join(["?" for x in headers])
                    ), rows)
            self.log("inserted %d rows into %s", len(rows), name)


            if headers == ["experiment", "key", "value"]:
                TableDictrows.update(rows)

        cur.execute("CREATE TABLE IF NOT EXISTS TableDict (experiment text, key text, value text,"
                    "UNIQUE (key) ON CONFLICT REPLACE)")
        cur.executemany("INSERT INTO TableDict (experiment, key, value) values(?,?,?)",
                        TableDictrows)
        self.log("inserted %d key-value pairs into TableDict", len(TableDictrows))
        cur.close()
        self.target.commit()

    def merge(self, update = True):
        """Do the actual merge operation"""
        self.collect_and_create_tables(drop = not update)
        self.collect_data()
        self.target.close()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(sys.argv[0] + " <target-database-file> [<source-db1> <source-db2> ...]")
        print(" -- merges different versuchung sqlite databases into a single one")
        sys.exit(-1)

    merger = Database_SQlite_Merger(sys.argv[1], sys.argv[2:])
    merger.merge()
