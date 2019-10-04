#!/usr/bin/env python

import setuptools

setuptools.setup (name = 'opendrift_landmask_data',
       version = '0.1rc2',
       description = 'Joined landmasks for GSHHS features used by cartopy',
       author = 'Gaute Hope',
       author_email = 'gaute.hope@met.no',
       url = 'http://github.com/OpenDrift/opendrift-landmask-data',
       packages = setuptools.find_packages(),
       package_data = { '': [ 'shapes/*.wkb' ] },
       setup_requires = ['setuptools_scm'],
       include_package_data = True
       )

