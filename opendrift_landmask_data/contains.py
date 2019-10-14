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

  def __init__(self, extent = None):
    """
    Initialize landmask from generated GeoTIFF

    Args:

      extent (array): [xmin, ymin, xmax, ymax]
    """
    self.extent = extent
    self.mask = np.memmap(GSHHSMask.maskmm, dtype = 'bool', mode = 'r', shape = (GSHHSMask.ny, GSHHSMask.nx))
    self.transform = GSHHSMask().transform().__invert__()

    # with rasterio.open(GSHHSMask.masktif, 'r') as src:
    #   self.mask = src.read(1)

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

    xm, ym = self.transform * (x, y)

    land = self.mask[ym.astype(np.int32), xm.astype(np.int32)]

    # checking against polygons
    # print ("checking against polys:", len(x[land]))
    if not skippoly and len(x[land]) > 0:

      if checkextent and self.extent is not None:
        assert np.all(shapely.vectorized.contains(self.extent, x[land], y[land])), "Points are not inside extent."

      land[land] = shapely.vectorized.contains(self.land, x[land], y[land])

    # print ("checked against poly.")

    return land


