#!/usr/bin/env python

import setuptools
from distutils.core import setup

setup (name = 'opendrift_landmask_data',
       version = '0.1.RC1',
       description = 'Joined landmasks for GSHHS features used by cartopy',
       author = 'Gaute Hope',
       author_email = 'gaute.hope@met.no',
       url = 'http://github.com/OpenDrift/opendrift-landmask-data',
       packages = ['opendrift_landmask_data'],
       package_data = { 'opendrift_landmask_data': [ 'shapes/*' ] },
       include_package_data = True
       )

