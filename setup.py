#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command
from distutils.spawn import spawn

from doc.conf import release, version

name = "versuchung"

print "version: " + version
print "release: " + release

try:
    from sphinx.setup_command import BuildDoc
    cmdclass = {'doc': BuildDoc}
except:
    print "No Sphinx installed (python-sphinx) so no documentation can be build"
    cmdclass = {}


class TestCommand(Command):
    user_options = []
    def run(self):
        spawn(["make", "-C", "tests"], verbose = 1)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

cmdclass["test"] = TestCommand

setup(name=name,
      version=version,
      description='a toolbox for experiments',
      author='Christian Dietrich',
      author_email='stettberger@dokucode.de',
      packages = ["versuchung"],
      package_dir = {'versuchung': 'src/versuchung'},
      cmdclass = cmdclass
      )
