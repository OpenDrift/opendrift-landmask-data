import pytest
import numpy as np

from opendrift_landmask_data.contains import Landmask

def test_setup_landmask(benchmark):
  l = benchmark(Landmask)

def test_landmask_contains():
  l = Landmask()

  onland = (np.array([15.]), np.array([65.6]))
  onocean = (np.array([5.]), np.array([65.6]))

  assert l.contains(onland[0], onland[1])
  assert not l.contains(onocean[0], onocean[1])

  l.contains([180], [90])
  l.contains([-180], [90])
  l.contains([180], [-90])
  l.contains([-180], [-90])

def test_landmask_onland(benchmark):
  l = Landmask()

  onland = (np.array([15.]), np.array([65.6]))
  benchmark(l.contains, onland[0], onland[1])

def test_landmask_onocean(benchmark):
  l = Landmask()

  onocean = (np.array([5.]), np.array([65.6]))
  benchmark(l.contains, onocean[0], onocean[1])

def test_landmask_many(benchmark):
  l = Landmask()

  x = np.arange(-180, 180, .5)
  y = np.arange(-90, 90, .5)

  xx, yy = np.meshgrid(x,y)

  print ("points:", len(xx.ravel()))
  benchmark(l.contains, xx.ravel(), yy.ravel())

