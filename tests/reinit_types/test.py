from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types import String, Optional, Bool, List

class BasicTypesTest(Experiment):
    inputs = {"string": String("A"),
              "bool"  : Bool(True),
              "string_optional": Optional(String()),
              'list'  : List(String, [])}

    def run(self):
        assert self.string.value == "X"
        assert self.bool.value == False
        assert self.string_optional.value == None


if __name__ == "__main__":
    import sys
    import shutil
    t = BasicTypesTest()
    dirname = t(["--string", "X", "--bool", "no", "--list", "a", "--list", "b"])

    reinit = BasicTypesTest(dirname)
    for field in ('string', 'bool', 'string_optional'):
        assert getattr(t, field).value == getattr(reinit, field).value,\
            "Field %s not correctly reinitted" % field

    assert [x.value for x in t.list.value] == [x.value for x in reinit.list.value], \
        "Field list not correctly reinitted"

    shutil.rmtree(dirname)
    print("success")
