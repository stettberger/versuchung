from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.tex import *

import pandas as pd

class TexTest(Experiment):
    outputs = {"tex": Macros("macro.tex"),
               "pgf": PgfKeyDict("pgf.tex"),
               "dref": DatarefDict("dref.tex"),
               "pd": DatarefDict("pandas.tex") }

    def run(self):
        tex = self.o.tex
        tex.macro("foo", "bar")
        tex.newline()
        tex.comment("barfoo")


        pgf = self.o.pgf

        pgf["foobar"] = 23
        self.dref["foobar"] = 42

        df = pd.DataFrame(data=[[1,2,3,'a'],
                                [4,2,6,'b'],
                                [7,1,9,'c'],
                                [0,1,2,'d']],
                          columns=['th', 'a', 'b', 'name'])

        # Test the Pandas Dumping
        self.pd.pandas(df)
        assert self.pd.get('0/b') == 3
        assert self.pd.get('0/name') == 'a'
        self.pd.clear()

        self.pd.pandas(df.set_index('th'))
        assert self.pd.get('7/name') == 'c'
        assert self.pd.get('4/b')    == 6
        self.pd.clear()

        self.pd.pandas(df.set_index('th'), names=True)
        assert self.pd.get('th=7/name') == 'c'
        assert self.pd.get('th=4/b')    == 6
        self.pd.clear()

        self.pd.pandas(df.set_index(['a', 'th']))
        assert self.pd.get('2/4/name') == 'b'
        assert self.pd.get('1/0/b')    == 2
        self.pd.clear()

        self.pd.pandas(df.set_index(['a', 'th']), names=['th'])
        assert self.pd.get('2/th=4/name') == 'b'
        assert self.pd.get('1/th=0/b')    == 2
        self.pd.clear()

        df.columns.name='col'

        self.pd.pandas(df.set_index(['a', 'th']), names=True)
        assert self.pd.get('a=2/th=4/col=name') == 'b'
        assert self.pd.get('a=1/th=0/col=b')    == 2
        self.pd.clear()

        self.pd.pandas(df.set_index(['a', 'th']).T, names=True)
        assert self.pd.get('col=name/a=2/th=4') == 'b'
        assert self.pd.get('col=b/a=1/th=0')    == 2
        self.pd.clear()

        self.pd.pandas(df.b.describe(), prefix='stat')
        assert self.pd.get('stat/min') == 2
        assert self.pd.get('stat/max') == 9
        assert self.pd.get('stat/50 percent') == 4.5
        self.pd.clear()

if __name__ == "__main__":
    import sys
    import shutil
    t = TexTest()
    dirname = t(sys.argv[1:])
    with open(dirname + "/macro.tex") as fd:
        content = fd.read()
        assert r'\newcommand{\foo} {bar}' in content
        assert "% barfoo" in content

    pgf = PgfKeyDict(dirname + "/pgf.tex")
    a = pgf.value
    assert len(pgf) == 1
    assert pgf["foobar"] == "23"

    dref = DatarefDict(dirname + "/dref.tex")
    a = dref.value
    assert len(dref) == 1
    assert dref["foobar"] == "42"

    shutil.rmtree(dirname)
    print("success")
