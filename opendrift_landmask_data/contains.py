import numpy as np
import shapely
import shapely.vectorized
import shapely.wkb as wkb
import shapely.strtree
from shapely.ops import unary_union
from shapely.geometry import box, MultiPolygon, Polygon
import rasterio
import cartopy
import mmap

from .mask import GSHHSMask
from .gshhs import GSHHS

class Landmask:
  land = None
  mask = None
  extent = None
  xm0 = 0
  ym0 = 0

  def __init__(self, extent = None):
    """
    Initialize landmask from generated GeoTIFF

    Args:

      extent (array): [xmin, ymin, xmax, ymax]
    """
    self.extent = extent
    self.mask = np.memmap(GSHHSMask.maskmm, dtype = 'bool', mode = 'r', shape = (GSHHSMask.ny, GSHHSMask.nx))

    with open(GSHHS['f'], 'rb') as fd:
      self.land = wkb.load(fd)

    if extent is not None:
      self.extent = box(*extent)
      rep_point = self.extent.representative_point()
      self.extent = shapely.prepared.prep(self.extent)

      # mask
      x0 = extent[0]; y0 = extent[1]
      x1 = extent[2]; y1 = extent[3]

      xm1, ym1 = self.xy2mask(x1, y1)
      self.xm0, self.ym0 = self.xy2mask(x0, y0)
      print (extent)
      print (self.xm0, xm1)
      print (self.ym0, ym1)
      print (self.mask.shape)
      self.mask = self.mask[self.ym0[0]:ym1[0]+1, self.xm0[0]:xm1[0]+1]
      print (self.mask.shape)

      # polygons
      self.land = MultiPolygon([l for l in self.land.geoms if self.extent.intersects(l)])

    else:
      self.extent = GSHHSMask.extent
      rep_point = self.extent.representative_point()
      self.extent = shapely.prepared.prep(self.extent)
      self.xm0, self.ym0, self.xm1, self.ym1 = tuple(*extent)

    self.land = shapely.prepared.prep(self.land)

    # warmup
    self.contains(rep_point.x, rep_point.y)

  def xy2mask(self, x, y):
    """ Mask indices for coordinates """
    if not isinstance(x, np.ndarray):
      x = np.array(x, ndmin = 1)

    if not isinstance(y, np.ndarray):
      y = np.array(y, ndmin = 1)

    assert len(x) == len(y)

    # wraps around
    xm = ((x - (-180)) / (180*2) * GSHHSMask.nx - 1 - self.xm0).astype(np.int32)

    # is reversed
    ym = np.abs((y - (-90)) / (90*2) * GSHHSMask.ny - 1 - self.ym0).astype(np.int32)

    return (xm, ym)

  def contains(self, x, y, skippoly = False, checkextent = True):
    """
    Check if coordinates x, y are on land

    Args:
      x (float, deg): longitude

      y (float, deg): latitude

      skippoly (bool): skip check against polygons

      checkextent (bool): check if points are within extent of landmask

    Returns:
      array of bools same length as x and y
    """
    if not isinstance(x, np.ndarray):
      x = np.array(x, ndmin = 1)

    if not isinstance(y, np.ndarray):
      y = np.array(y, ndmin = 1)

    if checkextent and self.extent is not None:
      assert np.all(shapely.vectorized.contains(self.extent, x, y)), "Points are not inside extent."

    xm, ym = self.xy2mask(x, y)
    land = self.mask[ym, xm]

    # checking against polygons
    # print ("checking against polys:", len(x[land]))
    if not skippoly and len(x[land]) > 0:
      land[land] = shapely.vectorized.contains(self.land, x[land], y[land])
    # print ("checked against poly.")

    return land


