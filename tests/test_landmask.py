import pytest
import numpy as np
import os
import tempfile

from opendrift_landmask_data import Landmask

tmpdir = os.path.join (tempfile.gettempdir(), 'landmask')
mmapf = os.path.join(tmpdir, 'mask.dat')

def delete_mask():
  print("deleting mask:", mmapf)
  if os.path.exists(mmapf):
    os.unlink(mmapf)

def test_generate_landmask():
  delete_mask()
  l = Landmask(__no_retry__ = True)

  assert os.path.exists(mmapf)

def test_concurrent_threads_landmask_generation():
  delete_mask()

  def f(i):
    print("launching instance:", i)
    l = Landmask(__concurreny_delay__ = 2., __no_retry__ = True)
    print("instance", i, "done")

  from concurrent.futures import ThreadPoolExecutor, wait
  with ThreadPoolExecutor(max_workers = 4) as exe:
    futures = [ exe.submit(f, i) for i in range(5) ]
    wait(futures)

def _f(i):
  print("launching instance:", i)
  l = Landmask(__concurrency_delay__ = 2., __no_retry__ = True)
  print("instance", i, "done")

def test_concurrent_processes_landmask_generation():
  delete_mask()

  from multiprocessing import Pool
  with Pool(processes = 4) as pool:
    pool.map(_f, range(5))

def _f2(i, abort):
  print("launching instance:", i)
  if abort:
    try:
      l = Landmask(__concurrency_delay__ = 2., __concurrency_abort__ = abort, __no_retry__ = True)
    except:
      pass
  else:
    l = Landmask(__concurrency_delay__ = 2., __concurrency_abort__ = abort, __no_retry__ = True)
  print("instance", i, "done")

def test_concurrent_process_abort_generation():
  delete_mask()

  from multiprocessing import Pool
  import time
  with Pool(processes = 2) as pool:
    r1 = pool.apply_async(_f2, (0, True))
    time.sleep(1)
    r2 = pool.apply_async(_f2, (1, False))

    r1.get(None)
    r2.get(None)

  assert os.path.exists(mmapf)

def test_setup_landmask_retry():
  delete_mask()
  import stat
  os.makedirs(tmpdir, exist_ok = True)
  m = os.stat(tmpdir).st_mode
  try:
    print("setting permissions on tmpdir to 0o000:", tmpdir)
    os.chmod(tmpdir, 0o000)
    l = Landmask()
  finally:
    os.chmod(tmpdir, m)

def test_setup_landmask_retry_open():
  delete_mask()
  l = Landmask(__retry_delete__ = True)

def test_setup_landmask_pregenerated(benchmark):
  delete_mask()
  l = Landmask(__no_retry__ = True)

  l = benchmark(Landmask)

def test_setup_landmask_generate(benchmark):
  def f():
    delete_mask()
    return Landmask(__no_retry__ = True)

  l = benchmark(f)

def test_landmask_contains():
  delete_mask()
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
  delete_mask()
  l = Landmask()

  onland = (np.array([15.]), np.array([65.6]))
  c = benchmark(l.contains, onland[0], onland[1])
  assert c

def test_landmask_onland_skippoly(benchmark):
  delete_mask()
  l = Landmask()

  onland = (np.array([15.]), np.array([65.6]))
  c = benchmark(l.contains, onland[0], onland[1], True)
  assert c

def test_landmask_onocean(benchmark):
  delete_mask()
  l = Landmask()

  onocean = (np.array([5.]), np.array([65.6]))
  c = benchmark(l.contains, onocean[0], onocean[1])
  assert not c

def test_landmask_onocean_skippoly(benchmark):
  delete_mask()
  l = Landmask()

  onocean = (np.array([5.]), np.array([65.6]))
  c = benchmark(l.contains, onocean[0], onocean[1], True)
  assert not c

def test_landmask_many(benchmark):
  delete_mask()
  l = Landmask()

  x = np.arange(-180, 180, .5)
  y = np.arange(-90, 90, .5)

  xx, yy = np.meshgrid(x,y)

  print ("points:", len(xx.ravel()))
  benchmark(l.contains, xx.ravel(), yy.ravel())

def test_landmask_many_extent(benchmark):
  delete_mask()
  l = Landmask([50, 0, 65, 40])

  x = np.linspace(50.1, 64.9, 30000)
  y = np.linspace(0.1, 39.9, 10)

  xx, yy = np.meshgrid(x,y)

  print ("points:", len(xx.ravel()))
  benchmark(l.contains, xx.ravel(), yy.ravel())

def test_norway(tmpdir):
  delete_mask()
  l = Landmask(extent=[-1, 44, 41, 68])

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

def test_tromsoe(tmpdir):
  delete_mask()

  # xmin, ymin, xmax, ymax
  extent=[18.64, 69.537, 19.37, 69.91]
  l = Landmask(extent)

  lon = np.arange (18.8, 18.969, .0003)
  lat = np.arange (69.59, 69.70, .0003)

  xx, yy = np.meshgrid(lon, lat)
  c = l.contains(xx.ravel(), yy.ravel(), True)
  c = c.reshape(xx.shape)

  print ("c:", c)

  import cartopy
  import cartopy.crs as ccrs
  import matplotlib.pyplot as plt
  import os
  plt.figure(dpi=200)
  ax = plt.axes(projection = ccrs.PlateCarree())
  # ax.contourf(lon, lat, c, transform = ccrs.PlateCarree())
  ax.imshow(c, extent = [ np.min(lon), np.max(lon), np.min(lat), np.max(lat)], transform=ccrs.PlateCarree())

  reader = cartopy.feature.GSHHSFeature('f') \
           .intersecting_geometries([
             extent[0],
             extent[2],
             extent[1],
             extent[3]])
  ax.add_geometries(list(reader), ccrs.PlateCarree(), alpha = .5)

  ax.coastlines()
  # ax.set_global()
  plt.savefig(os.path.join(tmpdir, 'tromsoe.png'))
  # plt.show()
