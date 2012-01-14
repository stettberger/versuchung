#!/usr/bin/env python

from distutils.core import setup
try:
    from sphinx.setup_command import BuildDoc
    cmdclass = {'doc': BuildDoc}
except:
    print "No Sphinx installed (python-sphinx) so no documentation can be build"
    cmdclass = {}


name = "versuchung"
version = "0.1"
release = "0.1.0"

setup(name=name,
      version=version,
      description='a toolbox for experiments',
      author='Christian Dietrich',
      author_email='stettberger@dokucode.de',
      packages = ["versuchung"],
      package_dir = {'versuchung': 'src/versuchung'},
      cmdclass = cmdclass
      )
