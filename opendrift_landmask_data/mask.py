import numpy as np
import shapely
import shapely.vectorized
import shapely.wkb as wkb
from shapely.geometry import box, MultiPolygon
import rasterio
import tempfile
import os
import os.path
import logging
import threading

from .gshhs import get_gshhs_f

class Landmask:
  extent = [-180, 180, -90, 90]
  epsg   = '32662' # Plate Carree

  ## minimum resolution:
  ## 0.269978 nm = .5 km, 1 deg <= 60 nm (at equator)
  nx  = 2*180*60*4
  ny  = 2*90*60*4
  dnm = 1./4.
  dm  = dnm * 1852.
  dx  = float(extent[1] - extent[0]) / nx
  dy  = float(extent[3] - extent[2]) / ny

  polys = None
  land = None
  mask = None
  transform = None
  invtransform = None

  tmpdir = os.path.join (tempfile.gettempdir(), 'landmask')
  mmapf = os.path.join(tmpdir, 'mask.dat')
  lockf = os.path.join(tmpdir, '.mask.dat.lock')

  generation_lock = threading.Lock()

  @staticmethod
  def get_mask():
    from pkg_resources import resource_stream
    masktif = os.path.join ('masks', 'mask_%.2f_nm.tif' % Landmask.dnm)
    return resource_stream (__name__, masktif)

  @staticmethod
  def get_transform():
    from rasterio import Affine
    x = [-180, 180]
    y = [-90, 90]
    resx = float(x[1] - x[0]) / Landmask.nx
    resy = float(y[1] - y[0]) / Landmask.ny
    return Affine.translation(x[0] - resx/2, y[0]-resy/2) * Affine.scale(resx, resy)

  def __32_bit__(self):
    import sys
    return sys.maxsize <= 2**32

  def __mask_exists__(self):
    return os.path.exists(self.mmapf)

  def __generate_impl__(self):
    if self.__32_bit__():
      raise Exception("numpy memory mapped file cannot exceed 2GB on 32 bit system")

    if not self.__mask_exists__():
      logging.info("generating memmap landmask from tif to %s.." % self.mmapf)

      with tempfile.NamedTemporaryFile(dir = self.tmpdir, delete = False) as fd:
        try:
          mask = np.memmap(fd, dtype = 'uint8', mode = 'w+', shape = (self.ny, self.nx))
          with rasterio.open(self.get_mask(), 'r') as src:
            src.read(1, out = mask)

          mask.flush()
          del mask

          if self.__concurreny_delay__:
            logging.warn("concurrency tesing, sleeping: %.2fs" % self.__concurreny_delay__)
            import time
            time.sleep(self.__concurreny_delay__)

          os.rename(fd.name, self.mmapf)
          logging.info("landmask generated")

        except:
          os.unlink(fd.name)
          raise

  def __generate__(self):
    if not os.path.exists(self.tmpdir):
      os.makedirs (self.tmpdir)

    if self.generation_lock.acquire(blocking = False):
      try:
        import fcntl

        with open(self.lockf, 'w') as fd:
          # try to get non-blocking lock, if fail, another process is presumably generating the
          # landmask. so we wait.
          try:
            logging.info("locking landmask for generation..")
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logging.info("got lock")

            # we got the lock, now generate mask
            self.__generate_impl__()

          except OSError:
            # file already locked
            logging.warn("landmask is being generated in another process, waiting for it to complete..")

            fcntl.lockf(fd, fcntl.LOCK_EX) # blocks

            logging.info("landmask generation done in another process, attempting to load..")

      except ImportError:
        logging.error("fcntl not available on this platform, concurrent generations of landmask (different threads or processes) might cause failing landmask generation. Make sure only one instance of landmask is running on system the first time.")
        self.__generate_impl__()

      finally:
        self.generation_lock.release()

    else:
      logging.info("landmask is being generated in another thread, waiting for it to complete..")
      self.generation_lock.acquire(True)
      self.generation_lock.release()
      logging.info("landmask generation done in another thread, attempting to load..")


  def __open_mask__(self):
    self.mask = np.memmap (self.mmapf, dtype = 'uint8', mode = 'r', shape = (self.ny, self.nx))

  def __init__(self, extent = None, skippoly = False, __concurreny_delay__ = 0):
    """
    Initialize landmask from generated GeoTIFF

    Args:

      extent (array): [xmin, ymin, xmax, ymax]
      skippoly (bool): do not load polygons

      __concurreny_delay__: internally used for race condition testing, do not use.
    """
    self.extent = extent
    self.transform = self.get_transform()
    self.invtransform = self.transform.__invert__()
    self.skippoly = skippoly
    self.__concurreny_delay__ = __concurreny_delay__

    if not self.__mask_exists__():
      self.__generate__()

    self.__open_mask__()

    if not skippoly:
      with get_gshhs_f() as fd:
        self.land = wkb.load(fd)

      if extent:
        self.extent = box(*extent)
        self.extent = shapely.prepared.prep(self.extent)

        # polygons
        self.land = MultiPolygon([l for l in self.land.geoms if self.extent.intersects(l)])

      self.polys = self.land
      self.land = shapely.prepared.prep(self.land)

  def contains(self, x, y, skippoly = None, checkextent = True):
    """
    Check if coordinates x, y are on land

    Args:
      x (scalar or array, deg): longitude

      y (scalar or array, deg): latitude

      skippoly (bool): skip check against polygons, default False unless constructed with True.

      checkextent (bool): check if points are within extent of landmask, default True

    Returns:

      array of bools same length as x and y
    """
    if skippoly is not None:
      assert not (not skippoly and self.skippoly), "cannot check against polygons when not constructed with polygons"
    else:
      skippoly = self.skippoly

    if not isinstance(x, np.ndarray):
      x = np.array(x, ndmin = 1, dtype = np.float32)

    if not isinstance(y, np.ndarray):
      y = np.array(y, ndmin = 1, dtype = np.float32)

    xm, ym = self.invtransform * (x, y)

    xm = xm.astype(np.int32)
    ym = ym.astype(np.int32)
    xm[xm==self.nx] = self.nx-1
    ym[ym==self.ny] = self.ny-1

    land = self.mask[ym, xm] == 1

    # checking against polygons
    if not skippoly and len(x[land]) > 0:

      if checkextent and self.extent is not None:
        assert np.all(shapely.vectorized.contains(self.extent, x[land], y[land])), "Points are not inside extent."

      land[land] = shapely.vectorized.contains(self.land, x[land], y[land])

    return land


