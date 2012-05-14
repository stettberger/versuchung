from versuchung.experiment import Experiment
from versuchung.types import String

class StringTest(Experiment):
    inputs = {"string": String("ABC")}

    def run(self):
        assert str(self.string) == "ABC"
        assert str(self.string) != repr(self.string)
        assert "<versuchung.types.String" in repr(self.string)
        assert "%s" % self.string == "ABC"

if __name__ == "__main__":
    import sys
    import shutil
    t = StringTest()
    dirname = t(sys.argv)
    shutil.rmtree(dirname)
    print "success"
