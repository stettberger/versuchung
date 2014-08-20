#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command
from distutils.spawn import spawn

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

version_info = {
    'name': 'versuchung',
    'version': '1.0',
    'description': 'A toolbox for experiments',
    'author': 'Christian Dietrich',
    'author_email': 'stettberger@dokucode.de',
    'url': 'http://github.de/stettberger/versuchung',
    'license': 'GPLv3',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.4' ],
}


setup(packages = ["versuchung"],
      package_dir = {'versuchung': 'src/versuchung'},
      cmdclass = cmdclass,
      **version_info
  )
