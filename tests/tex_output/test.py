from versuchung.experiment import Experiment
from versuchung.tex import Macros, PgfKeyDict

class TexTest(Experiment):
    outputs = {"tex": Macros("macro.tex"),
               "pgf": PgfKeyDict("pgf.tex")}

    def run(self):
        tex = self.o.tex
        tex.macro("foo", "bar")
        tex.newline()
        tex.comment("barfoo")


        pgf = self.o.pgf

        pgf["foobar"] = 23


if __name__ == "__main__":
    import sys
    import shutil
    t = TexTest()
    dirname = t(sys.argv)
    with open(dirname + "/macro.tex") as fd:
        content = fd.read()
        assert r'\newcommand{\foo} {bar}' in content
        assert "% barfoo" in content

    pgf = PgfKeyDict(dirname + "/pgf.tex")
    a = pgf.value
    assert len(pgf) == 1
    assert pgf["foobar"] == "23"


    shutil.rmtree(dirname)
    print "success"
