#!/usr/bin/env python3

from setuptools import setup, Command

import sys

try:
    from sphinx.setup_command import BuildDoc
    cmdclass = {'doc': BuildDoc}
except:
    print("No Sphinx installed (python-sphinx) so no documentation can be build")
    cmdclass = {}


class TestCommand(Command):
    user_options = []
    def run(self):
        self.spawn(["make", "-C", "tests", "PYTHON=%s" % (sys.executable,)])

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

cmdclass["test"] = TestCommand

with open("README.md", "r") as fh:
    long_description = fh.read()

version_info = {
    'name': 'versuchung',
    'version': '1.3.5',
    'description': 'A toolbox for experiments',
    'author': 'Christian Dietrich',
    'author_email': 'stettberger@dokucode.de',
    'url': 'http://github.de/stettberger/versuchung',
    'long_description': long_description,
    'long_description_content_type': "text/markdown",
    'license': 'GPLv3',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5'
    ],
    'include_package_data': True,
}


setup(packages = ["versuchung"],
      package_dir = {'versuchung': 'src/versuchung'},
      cmdclass = cmdclass,
      **version_info
  )
