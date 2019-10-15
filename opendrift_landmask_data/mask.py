import numpy as np
import shapely
import shapely.vectorized
import shapely.wkb as wkb
from shapely.geometry import box, MultiPolygon
import rasterio
import tempfile
import os
import os.path

from .gshhs import GSHHS
mask = os.path.join(os.path.dirname(__file__), 'masks') + os.path.sep

class Landmask:
  extent = [-180, 180, -90, 90]
  epsg   = '32662' # Plate Carree

  ## minimum resolution:
  ## 0.269978 nm = .5 km, 1 deg <= 60 nm (at equator)
  nx = 2*180*60*4
  ny = 2*90*60*4
  dnm = 1/4
  dm     = dnm * 1852.
  dx     = (extent[1] - extent[0])/nx
  dy     = (extent[3] - extent[2])/ny
  maskmm  = os.path.join (mask, 'mask_%.2f_nm.mm' % dnm)
  masktif = os.path.join (mask, 'mask_%.2f_nm.tif' % dnm)

  land = None
  mask = None
  transform = None
  invtransform = None

  @staticmethod
  def get_transform():
    from rasterio import Affine
    x = [-180, 180]
    y = [-90, 90]
    resx = float(x[1] - x[0]) / Landmask.nx
    resy = float(y[1] - y[0]) / Landmask.ny
    return Affine.translation(x[0] - resx/2, y[0]-resy/2) * Affine.scale(resx, resy)

  def __init__(self, extent = None):
    """
    Initialize landmask from generated GeoTIFF

    Args:

      extent (array): [xmin, ymin, xmax, ymax]
    """
    self.extent = extent
    self.transform = self.get_transform()
    self.invtransform = self.transform.__invert__()

    tmpdir = os.path.join (tempfile.gettempdir(), 'landmask')
    if not os.path.exists(tmpdir): os.makedirs (tmpdir)

    mmapf = os.path.join(tmpdir, 'mask.dat')
    if not os.path.exists (mmapf):
      print ("generating memmap landmask from tif..")
      self.mask  = np.memmap (mmapf, dtype = 'uint8', mode = 'w+', shape = (self.ny, self.nx))

      with rasterio.open(self.masktif, 'r') as src:
        src.read(1, out = self.mask)

      del self.mask

    self.mask  = np.memmap (mmapf, dtype = 'uint8', mode = 'r', shape = (self.ny, self.nx))

    with open(GSHHS['f'], 'rb') as fd:
      self.land = wkb.load(fd)

    if extent:
      self.extent = box(*extent)
      rep_point = self.extent.representative_point()
      self.extent = shapely.prepared.prep(self.extent)

      # polygons
      self.land = MultiPolygon([l for l in self.land.geoms if self.extent.intersects(l)])

    self.land = shapely.prepared.prep(self.land)

    # warmup
    if extent:
      self.contains(rep_point.x, rep_point.y)
    else:
      self.contains(0, 0)

  def contains(self, x, y, skippoly = False, checkextent = True):
    """
    Check if coordinates x, y are on land

    Args:
      x (scalar or array, deg): longitude

      y (scalar or array, deg): latitude

      skippoly (bool): skip check against polygons, default False

      checkextent (bool): check if points are within extent of landmask, default True

    Returns:

      array of bools same length as x and y
    """
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


