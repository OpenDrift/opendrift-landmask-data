import numpy as np
import shapely.vectorized
import shapely.wkb as wkb
import shapely.strtree
from shapely.geometry import box, MultiPolygon
import rasterio

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

    # self.mask = np.load(GSHHSMask.masknpy, mmap_mode = 'r')
    with rasterio.open(GSHHSMask.masktif, 'r') as src:
      self.mask = src.read(1)

    with open (GSHHS['f'], 'rb') as fd:
      self.land = wkb.load(fd)

      if extent is not None:
        tree = shapely.strtree.STRtree(self.land.geoms)
        self.extent = box(*extent)
        lands = MultiPolygon(tree.query(self.extent))
        self.extent = shapely.prepared.prep(self.extent)
        self.land = shapely.prepared.prep(lands)
      else:
        self.land = shapely.prepared.prep(self.land)

  def contains(self, x, y):
    """
    Check if coordinates x, y are on land

    Args:
      x (float, deg): longitude
      y (float, deg): latitude

    Returns:
      array of bools same length as x and y
    """
    if not isinstance(x, np.ndarray):
      x = np.array(x, ndmin = 1)

    if not isinstance(y, np.ndarray):
      y = np.array(y, ndmin = 1)

    assert len(x) == len(y)

    xm = (x - (-180)) / (180*2) * (GSHHSMask.nx - 1)
    ym = (y - (-90)) / (90*2) * (GSHHSMask.ny - 1)

    # print ("checking:", x, y, " -> ", xm, ym)
    land = self.mask[ym.astype(np.int32), xm.astype(np.int32)] == 1

    # checking against polygons
    if self.extent is not None:
      assert np.all(shapely.vectorized.contains(self.extent, x[land], y[land]))

    land[land] = shapely.vectorized.contains(self.land, x[land], y[land])

    return land

