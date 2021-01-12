#!/usr/bin/env python

import os
import setuptools
from setuptools.command.build_py import build_py as BuildPy

class BuildPyCommand(BuildPy):
  def unpack(self):
    if not os.path.exists('opendrift_landmask_data/shapes/gshhs_f_-180.000000E-90.000000N180.000000E90.000000N.wkb'):
      import bz2
      import shutil

      print ("decompressing 'full' resolution coastline..")

      with bz2.BZ2File('opendrift_landmask_data/shapes/compressed/gshhs_f_-180.000000E-90.000000N180.000000E90.000000N.wkb.bz2', 'r') as cf:

        with open('opendrift_landmask_data/shapes/gshhs_f_-180.000000E-90.000000N180.000000E90.000000N.wkb', 'wb') as uf:
          shutil.copyfileobj(cf, uf)

  def run(self):
    self.unpack()
    setuptools.command.build_py.build_py.run(self)

setuptools.setup (name = 'opendrift_landmask_data',
       version = '0.7',
       description = 'Joined landmasks for GSHHS features used by cartopy',
       author = 'Gaute Hope',
       author_email = 'gaute.hope@met.no',
       url = 'http://github.com/OpenDrift/opendrift-landmask-data',
       packages = setuptools.find_packages(exclude = ['*.compressed']),
       package_data = { '': [ 'shapes/*.wkb', 'masks/*.tif', 'masks/*.xz' ] },
       include_package_data = False,
       setup_requires = [ 'setuptools_scm' ],
       extra_require = {
         'contains': [ 'shapely[vectorized]',
                       'numpy',
                       'affine' ]
                       },
       cmdclass = { 'build_py': BuildPyCommand }
       )

