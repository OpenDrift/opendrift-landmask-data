import numpy as np
import shapely
import shapely.vectorized
import shapely.wkb as wkb
from shapely.geometry import box, MultiPolygon
import rasterio
import tempfile
import os
import os.path

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

  @staticmethod
  def get_mask():
    from pkg_resources import resource_stream
    masktif = os.path.join ('masks', 'mask_%.2f_nm.tif' % dnm)
    return resource_stream (__name__, masktif)

  @staticmethod
  def get_transform():
    from rasterio import Affine
    x = [-180, 180]
    y = [-90, 90]
    resx = float(x[1] - x[0]) / Landmask.nx
    resy = float(y[1] - y[0]) / Landmask.ny
    return Affine.translation(x[0] - resx/2, y[0]-resy/2) * Affine.scale(resx, resy)

  def __init__(self, extent = None, skippoly = False):
    """
    Initialize landmask from generated GeoTIFF

    Args:

      extent (array): [xmin, ymin, xmax, ymax]
      skippoly (bool): do not load polygons
    """
    self.extent = extent
    self.transform = self.get_transform()
    self.invtransform = self.transform.__invert__()
    self.skippoly = skippoly

    tmpdir = os.path.join (tempfile.gettempdir(), 'landmask')
    if not os.path.exists(tmpdir): os.makedirs (tmpdir)

    mmapf = os.path.join(tmpdir, 'mask.dat')
    if not os.path.exists (mmapf):
      print ("generating memmap landmask from tif..")
      self.mask  = np.memmap (mmapf, dtype = 'uint8', mode = 'w+', shape = (self.ny, self.nx))

      with rasterio.open(self.get_mask(), 'r') as src:
        src.read(1, out = self.mask)

      del self.mask

    self.mask  = np.memmap (mmapf, dtype = 'uint8', mode = 'r', shape = (self.ny, self.nx))

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


