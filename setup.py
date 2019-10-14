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

      with bz2.open('opendrift_landmask_data/shapes/compressed/gshhs_f_-180.000000E-90.000000N180.000000E90.000000N.wkb.bz2', 'r') as cf:

        with open('opendrift_landmask_data/shapes/gshhs_f_-180.000000E-90.000000N180.000000E90.000000N.wkb', 'wb') as uf:
          shutil.copyfileobj(cf, uf)

  def generate_mask(self):
    from opendrift_landmask_data.mask import GSHHSMask

    if not os.path.exists(GSHHSMask.maskmm):
      if not os.path.exists (os.path.dirname(GSHHSMask.maskmm)):
        os.makedirs (os.path.dirname(GSHHSMask.maskmm))
      from opendrift_landmask_data.rasterize import gshhs_rasterize, mask_rasterize
      from opendrift_landmask_data.gshhs import GSHHS

      print ("generating raster at %.2f m resolution (this might take a couple of minutes).." % GSHHSMask.dm)

      # gshhs_rasterize(GSHHS['f'], 'opendrift_landmask_data/masks/mask_%.2f_nm.tif' % GSHHSMask.dnm)
      mask_rasterize(GSHHS['f'], 'opendrift_landmask_data/masks/mask_%.2f_nm.mm' % GSHHSMask.dnm)

  def run(self):
    self.unpack()
    self.generate_mask()
    setuptools.command.build_py.build_py.run(self)

setuptools.setup (name = 'opendrift_landmask_data',
       version = '0.1rc6',
       description = 'Joined landmasks for GSHHS features used by cartopy',
       author = 'Gaute Hope',
       author_email = 'gaute.hope@met.no',
       url = 'http://github.com/OpenDrift/opendrift-landmask-data',
       packages = setuptools.find_packages(exclude = ['*.compressed']),
       package_data = { '': [ 'shapes/*.wkb', 'masks/*.mm' ] },
       include_package_data = False,
       setup_requires = [ 'setuptools_scm',
                          'rasterio >= 1.0',
                          'shapely[vectorized]',
                          'numpy'
                        ],
       extra_require = {
         'contains': [ 'rasterio >= 1.0',
                       'shapely[vectorized]',
                       'numpy' ]
                       },
       cmdclass = { 'build_py': BuildPyCommand }
       )

