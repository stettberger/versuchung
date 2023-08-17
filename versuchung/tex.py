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

import json
import re
import os
import luadata

from versuchung.files import File


class Macros(File):
    """Can be used as: **input parameter** and **output parameter**

    A Macros file is a normal :class:`~versuchung.files.File` with the
    extension, that you can define TeX macros easily. This is
    especially useful for writing texts. You may have a experiment,
    which may be an analysis to an experiment that produces raw
    data. The produced numbers should appear in your LaTeX
    document. So instead of copying the numbers you can define TeX
    macros and use them in the text. This is especially useful if you
    work on the experiment and the text in parallel and the numbers
    change often.

    >>> from versuchung.tex import Macros
    >>> macro = Macros("/tmp/test.tex")
    >>> macro.macro("MyNewTexMacro", 23)
    >>> print macro.value
    \\newcommand{\\MyNewTexMacro} {23}

    """
    def __init__(self, filename = "data.tex"):
        """Define tex macros directly as output of a experiment.

        Use this only as output parameter!."""
        File.__init__(self, filename)

    def macro(self, macro, value):
        """Define a new tex macro with \\\\newcommand. This will result in::

            \\newcommand{%(macro)s} { %(value)s}

        """

        self.write("\\newcommand{\\%s} {%s}\n" % (macro, value), append = True)

    def comment(self, comment):
        """Add a comment in the macro file"""
        for line in comment.split("\n"):
            self.write("%% %s\n" % line.strip(), append = True)

    def newline(self):
        """Append an newline to the texfile"""
        self.write("\n", append = True)


class PgfKeyDict(File, dict):
    """Can be used as: **input parameter** and **output parameter**

    PgfKeyDict is very similar to :class:`~versuchung.tex.Macros`, but
    instead of \\\\newcommand directives it uses pgfkeys, can be used
    as a ``dict`` and it is possible to read it in again to produce
    the (almost) same dict again.

    >>> from versuchung.tex import PgfKeyDict
    >>> pgf = PgfKeyDict("/tmp/test.tex")
    >>> pgf["abcd"] = 23
    >>> pgf.flush()  # flush method of File
    >>> print(open("/tmp/test.tex").read())
    \\pgfkeyssetvalue{/versuchung/abcd}{23}

    In the TeX source you can do something like::

      \\usepackage{tikz}
      \\pgfkeys{/pgf/number format/.cd,fixed,precision=1}
      [...]
      \\newcommand{\\versuchung}[1]{\\pgfkeysvalueof{/versuchung/#1}}
      \\versuchung{abcd}

    .. note::

       It is better to use :class:`PgfKeyDict` instead of :class:`Macros`, because
       you can also use spaces and other weird characters in pgfkeys,
       which cannot be used in TeX macro names.
    """

    def __init__(self, filename = "data.tex", pgfkey = "/versuchung", setmacro="pgfkeyssetvalue"):
        File.__init__(self, filename)
        dict.__init__(self)

        self.__pgfkey = pgfkey
        self.format_string = "\\" + setmacro + "{%s/%s}{%s}"

        # Ensure the file is written
        if os.path.exists(self.path):
            a = self.value


    def after_read(self, value):
        regex = self.format_string %(self.__pgfkey,"([^{}]*)", "([^{}]*)")
        regex = regex.replace('\\', r'\\')
        for line in value.split("\n"):
            m = re.search(regex, line)
            if m:
                self[m.groups()[0]] = m.groups()[1]
        return self

    def before_write(self, value):
        v = []
        last_base_key = None
        for key in sorted(self):
            value = self[key]
            if "/" in key:
                base_key = key[:key.rindex("/")]
            else:
                base_key = None
            if last_base_key and last_base_key != base_key:
                v.append("")
            last_base_key = base_key
            v.append(self.format_string % (self.__pgfkey, key, value))

        return "\n".join(v) + "\n"

    def flush(self):
        self.value = self.before_write(self)
        File.flush(self)

    class PrefixForPgfKeyDict:
        def __init__(self, prefix, d):
            self.prefix = prefix
            self.d = d
        def __getitem__(self, key):
            return self.d[self.prefix + key]
        def __setitem__(self, key, value):
            self.d[self.prefix + key] = value
        def __delitem__(self, key):
            del self.d[self.prefix + key]
        def prefixed_with(self, prefix):
            return self.d.PrefixForPgfKeyDict(self.prefix + prefix, self.d)

    def prefixed_with(self, prefix):
        return self.PrefixForPgfKeyDict(prefix, self)

    def pandas(self, df, prefix="", names=None, verbose=False):
        """Import pandas.DataFrame or pandas.Series as keys

        This functions imports all cells from a DataFrame or Series as
        individual keys. The key is generated from the index and the
        columns (lines first, columns second). MultiIndex is supported
        for both dimension. For example, for the following DataFrame

           >>> import pandas as pd
           >>> df = pd.DataFrame([[1,1,1], [4, 1.5, 4]], columns=['th', 'speedup', 'load'])
           >>> df = df.set_index('th')
           >>> df
               speedup  load
           th
           1       1.0     1
           4       1.5     4
           >>> from versuchung.tex import PgfKeyDict
           >>> pgf = PgfKeyDict("/tmp/test.tex")
           >>> pgf.pandas(df, names=['th'], verbose=True)
           th=1/speedup => 1.0
           th=1/load => 1.0
           th=4/speedup => 1.5
           th=4/load => 4.0

        With the ``names`` parameter, you can control whether a level
        should be prefixed with the index name. In the above example,
        ``th=`` is the result of the names parameter. A useful pattern
        is to ``describe()`` a column:

          >>> pgf.pandas(df.speedup.describe(), prefix="speedup", verbose=True)
          speedup/count => 2.0
          speedup/mean => 1.25
          speedup/std => 0.3535533905932738
          speedup/min => 1.0
          speedup/25 percent => 1.125
          speedup/50 percent => 1.25
          speedup/75 percent => 1.375
          speedup/max => 1.5
        """
        import pandas as pd

        if prefix: prefix += "/"
        else:      prefix = ""

        def wrap_list(seq):
            if hasattr(seq, "__iter__") and not type(seq) is str:
                return seq
            return [seq]

        def zip_extend(a, b):
            a_len, b_len = len(a), len(b)
            ret_len = max(a_len, b_len)
            return zip(list(a) + [None] * (ret_len - a_len), list(b) + [None] * (ret_len - b_len))

        def fmt(name, key):
            ret = []
            for k, v in zip_extend(wrap_list(name), wrap_list(key)):
                # print(names, k, hasattr(names, "__contains__") and k in names)
                if k is not None and names == True or (hasattr(names, "__contains__") and k in names):
                    ret.append(f"{k}={v}")
                else:
                    ret.append(str(v))
            return "/".join(ret)

        if isinstance(df, pd.DataFrame):
            for index, row in df.iterrows():
                pp = fmt(df.index.name or df.index.names, index)
                self.pandas(row, prefix=prefix+pp, names=names, verbose=verbose)
        elif isinstance(df, pd.Series):
            for key in df.index:
                pp = fmt(df.index.name or df.index.names, key)
                dref_key = (prefix + pp).replace("%", " percent")
                if verbose: print(f"{dref_key} => {df.loc[key]}")
                self[dref_key] = df.loc[key]
        else:
            raise ValueError("Please supply a pandas.DataFrame or pandas.Series")


class DatarefDict(PgfKeyDict):
    """Can be used as: **input parameter** and **output parameter**

    DatarefDict is like :class:`~versuchung.tex.PgfKeyDict`, but generates keys for dataref <https://ctan.org/pkg/dataref>.

    In LaTeX, you can reference dataref keys or calculate with them::

        \\dref{/base}
        \\drefrel[percent of=/base]{/derived}

    """

    def __init__(self, filename = "data.tex", key = ""):
        PgfKeyDict.__init__(self, filename, key, "drefset")


class _InnerLuaTable(dict):
    """Used for nested LuaTables.

    Please refer to the :class:`~versuchung.tex.LuaTable` for documentation."""
    def __init__(self):
        dict.__init__(self)

    def __setitem__(self, key, value, /):
        if not isinstance(value, (str, int, float, bool, _InnerLuaTable)):
            raise ValueError("Value must be one of str, int, float or bool.")
        if not isinstance(key, (str, int)):
            raise ValueError("Key must be a str or int.")
        if isinstance(key, str) and " " in key:
            raise ValueError("Key is not allowed to contain spaces.")
        dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if key not in self:
            # assume a key chain
            self[key] = _InnerLuaTable()
        return dict.__getitem__(self, key)

    def _to_lua(self, indent=0):
        return luadata.serialize(self, indent=' ' * indent).split('\n')


class LuaTable(File, _InnerLuaTable):
    """Can be used as: **input parameter** and **output parameter**

    When using Lua(La)TeX or lmtx (from ConTeXt), TeX is able to interact with Lua.
    This class exports the data as a lua table, so it can be accessed from TeX via Lua.

    >>> from versuchung.tex import LuaTable
    >>> lua = LuaTable("/tmp/table.lua")
    >>> lua["some"]["key"] = 5
    >>> lua.flush()  # flush method of File
    >>> print(open("/tmp/table.lua").read())
    userdata = userdata or {}
    userdata.experiment = {
      some = {
        key = 5
      }
    }

    In ConTeXt, you can access the table with something like::

        \\startluacode
        require("table.lua")
        \\stopluacode

        \\starttext
        \\ctxlua{context(userdata.experiment.some.key)}
        \\stoptext

    In LuaLaTeX source you can do something like::

        \\documentclass{article}

        \\usepackage{luacode}
        \\luadirect{require("table.lua")}

        \\begin{document}
            \\luadirect{tex.print(userdata.experiment.some.key)}
        \\end{document}

    .. note::

       If you want to calculate with the data even more and want to do that in
       your TeX project, a Lua table might be the best choice since you can
       use everything from Lua to use the data.
    """
    def __init__(self, filename="data.lua", experiment_name="experiment"):
        File.__init__(self, filename)
        _InnerLuaTable.__init__(self)
        self.experiment_name = experiment_name

        # Ensure the file is written
        if os.path.exists(self.path):
            _ = self.value

    @staticmethod
    def _to_versuchung_objects(data):
        if isinstance(data, dict):
            tab = _InnerLuaTable()
            for key, value in data.items():
                tab[key] = LuaTable._to_versuchung_objects(value)
            return tab
        if isinstance(data, list):
            tab = _InnerLuaTable()
            for idx, item in enumerate(data):
                tab[idx + 1] = LuaTable._to_versuchung_objects(item)
            return tab
        return data

    def after_read(self, value):
        # first drop the header
        val = value[value.find("= {") + 2:]
        parsed = luadata.unserialize(val)
        for key, value in parsed.items():
            self[key] = self._to_versuchung_objects(value)

    def before_write(self, value):
        header = ("userdata = userdata or {}\n"
                  f"userdata.{self.experiment_name} = ")
        return header + "\n".join(self._to_lua(indent=2))

    def flush(self):
        self.value = self.before_write(self)
        File.flush(self)

    def __repr__(self):
        return f"LuaTable({' '.join(self._to_lua())})"


if __name__ == '__main__':
    import sys
    print(PgfKeyDict(sys.argv[1]))
