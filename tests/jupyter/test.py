#!/usr/bin/python3

from versuchung.__main__ import main
import os

if __name__ == "__main__":
    import shutil
    dirname = main(["test.ipynb", "--arg0", "23"])
    fn = os.path.join(dirname, "data.dref")
    with open(fn) as fd:
        content = fd.read()
        assert r'\drefset{/a}{23}' in content
    assert os.path.exists(os.path.join(dirname, "test.ipynb"))
    assert os.path.exists(os.path.join(dirname, "test.ipynb.html"))
    shutil.rmtree(dirname)
    print("success")

