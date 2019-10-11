import pytest
import numpy as np

from opendrift_landmask_data.contains import Landmask

def test_setup_landmask(benchmark):
  l = benchmark(Landmask)

def test_landmask_contains():
  l = Landmask()

  onland = (np.array([15.]), np.array([65.6]))
  assert l.contains(onland[0], onland[1])

  onland = (np.array([10.]), np.array([60.0]))
  assert l.contains(onland[0], onland[1])

  onocean = (np.array([5.]), np.array([65.6]))
  assert not l.contains(onocean[0], onocean[1])

  l.contains([180], [90])
  l.contains([-180], [90])
  l.contains([180], [-90])
  l.contains([-180], [-90])

def test_landmask_onland(benchmark):
  l = Landmask()

  onland = (np.array([15.]), np.array([65.6]))
  c = benchmark(l.contains, onland[0], onland[1])
  assert c

def test_landmask_onocean(benchmark):
  l = Landmask()

  onocean = (np.array([5.]), np.array([65.6]))
  c = benchmark(l.contains, onocean[0], onocean[1])
  assert not c

def test_landmask_many(benchmark):
  l = Landmask()

  x = np.arange(-180, 180, .5)
  y = np.arange(-90, 90, .5)

  xx, yy = np.meshgrid(x,y)

  print ("points:", len(xx.ravel()))
  benchmark(l.contains, xx.ravel(), yy.ravel())

def test_landmask_many_extent(benchmark):
  l = Landmask([50, 0, 52, 10])

  x = np.linspace(50.1, 64.9, 30000)
  y = np.linspace(0.1, 39.9, 10)

  xx, yy = np.meshgrid(x,y)

  print ("points:", len(xx.ravel()))
  benchmark(l.contains, xx.ravel(), yy.ravel())

def test_norway(tmpdir):
  l = Landmask(extent=[0, 45, 40, 67])

  lon = np.arange (0, 40, .1)
  lat = np.arange (45, 67, .1)

  xx, yy = np.meshgrid(lon, lat)
  c = l.contains(xx.ravel(), yy.ravel())
  c = c.reshape(xx.shape)

  print ("c:", c)

  import cartopy.crs as ccrs
  import matplotlib.pyplot as plt
  import os
  plt.figure(dpi=200)
  ax = plt.axes(projection = ccrs.PlateCarree())
  # ax.contourf(lon, lat, c, transform = ccrs.PlateCarree())
  ax.imshow(c, extent = [ 0, 40, 45, 67], transform=ccrs.PlateCarree())
  ax.coastlines()
  ax.set_global()
  plt.savefig(os.path.join(tmpdir, 'norway.png'))
  # plt.show()
