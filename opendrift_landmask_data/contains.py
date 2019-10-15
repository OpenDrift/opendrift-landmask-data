import numpy as np
import shapely
import shapely.vectorized
import shapely.wkb as wkb
from shapely.geometry import box, MultiPolygon
import rasterio
import tempfile
import os
import os.path

from .mask import GSHHSMask
from .gshhs import GSHHS

class Landmask:
  land = None
  mask = None
  extent = None
  transform = None

  def __init__(self, extent = None):
    """
    Initialize landmask from generated GeoTIFF

    Args:

      extent (array): [xmin, ymin, xmax, ymax]
    """
    self.extent = extent
    self.transform = GSHHSMask().transform.__invert__()

    tmpdir = os.path.join (tempfile.gettempdir(), 'landmask')
    if not os.path.exists(tmpdir): os.makedirs (tmpdir)

    mmapf = os.path.join(tmpdir, 'mask.dat')
    if not os.path.exists (mmapf):
      print ("generating memmap landmask from tif..")
      self.mask  = np.memmap (mmapf, dtype = 'uint8', mode = 'w+', shape = (GSHHSMask.ny, GSHHSMask.nx))

      with rasterio.open(GSHHSMask.masktif, 'r') as src:
        src.read(1, out = self.mask)

      del self.mask

    self.mask  = np.memmap (mmapf, dtype = 'uint8', mode = 'r', shape = (GSHHSMask.ny, GSHHSMask.nx))

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
      x = np.array(x, ndmin = 1)

    if not isinstance(y, np.ndarray):
      y = np.array(y, ndmin = 1)

    xm, ym = self.transform * (x, y)

    land = self.mask[ym.astype(np.int32), xm.astype(np.int32)] == 1

    # checking against polygons
    if not skippoly and len(x[land]) > 0:

      if checkextent and self.extent is not None:
        assert np.all(shapely.vectorized.contains(self.extent, x[land], y[land])), "Points are not inside extent."

      land[land] = shapely.vectorized.contains(self.land, x[land], y[land])

    return land


