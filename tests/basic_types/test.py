from __future__ import print_function

from versuchung.experiment import Experiment
from versuchung.types import String, Optional, Bool

class BasicTypesTest(Experiment):
    inputs = {"string": String("ABC"),
              "bool"  : Bool(True),
              "string_optional": Optional(String())}

    def run(self):
        assert not self.string_optional.was_given()
        assert self.string.was_given()

        assert str(self.string) == "ABC"
        assert str(self.string) != repr(self.string)
        assert "<versuchung.types.String" in repr(self.string)
        assert "%s" % self.string == "ABC"
        assert self.bool.value == False


if __name__ == "__main__":
    import sys
    import shutil
    t = BasicTypesTest()
    dirname = t(["--bool", "no"] + sys.argv)
    shutil.rmtree(dirname)
    print("success")
