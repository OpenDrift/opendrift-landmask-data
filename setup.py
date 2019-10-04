#!/usr/bin/env python

from distutils.core import setup
import setuptools.command.build_py
import tarfile


class BuildPyCommand(setuptools.command.build_py.build_py):
  def unpack(self):
    with tarfile.open('opendrift_landmask_data/shapes.tar.xz', 'r:xz') as t:
      t.extractall('opendrift_landmask_data/')

  def run(self):
    self.unpack()
    setuptools.command.build_py.build_py.run(self)

setup (name = 'opendrift_landmask_data',
       version = '0.1',
       description = 'Joined landmasks for GSHHS and NaturalEarth features used by cartopy',
       author = 'Gaute Hope',
       author_email = 'gaute.hope@met.no',
       url = 'http://github.com/OpenDrift/opendrift-landmask-data',
       packages = ['opendrift_landmask_data'],
       package_data = { 'opendrift_landmask_data': [ 'shapes/*' ] },
       include_package_data = True,
       cmdclass = { 'build_py': BuildPyCommand }
       )

