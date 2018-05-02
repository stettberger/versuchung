from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types import String, Optional, Bool, List

class ReinitTypesTest(Experiment):
    inputs = {"string": String("A"),
              "bool"  : Bool(True),
              "string_optional": Optional(String()),
              'list'  : List(String, [])}

    def run(self):
        assert self.string.value == "X"
        assert self.bool.value == False
        assert self.string_optional.value == None


class DownstreamReinitTypesTest(Experiment):
    inputs = {'reinit': ReinitTypesTest('ReinitTypesTest-Foobar') }

    def run(self):
        do_asserts(self.reinit)

def do_asserts(reinit):
    global t

    for field in ('string', 'bool', 'string_optional'):
        assert getattr(t, field).value == getattr(reinit, field).value,\
            "Field %s not correctly reinitted" % field

    assert [x.value for x in t.list.value] == [x.value for x in reinit.list.value], \
        "Field list not correctly reinitted"


if __name__ == "__main__":
    import sys
    import shutil
    t = ReinitTypesTest()
    dirname = t(["--string", "X", "--bool", "no", "--list", "a", "--list", "b"])

    # Reinit without enclosing experiment
    reinit = ReinitTypesTest(dirname)
    do_asserts(reinit)

    t2 = DownstreamReinitTypesTest()
    dirname2 = t2(['--reinit', dirname])
    reinit2 = DownstreamReinitTypesTest(dirname2)
    do_asserts(reinit2.reinit)

    shutil.rmtree(dirname)
    print("success")
