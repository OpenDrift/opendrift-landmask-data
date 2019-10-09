import numpy as np
import shapely.vectorized
import shapely.wkb as wkb
import pyproj

from .mask import GSHHSMask
from .gshhs import GSHHS

class Landmask:
  land = None
  mask = None

  def __init__(self):
    self.mask = np.load(GSHHSMask.maskf, mmap_mode = 'r')

    with open (GSHHS['f'], 'rb') as fd:
      self.land = shapely.prepared.prep(wkb.load(fd))

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
      x = np.array(x)

    if not isinstance(y, np.ndarray):
      y = np.array(y)

    assert len(x) == len(y)

    xm = (x - (-180)) / (180*2) * (GSHHSMask.nx - 1)
    ym = (y - (-90)) / (90*2) * (GSHHSMask.ny - 1)

    # print ("checking:", x, y, " -> ", xm, ym)
    land = self.mask[ym.astype(np.int32), xm.astype(np.int32)]

    # checking against polygons
    land[land] = shapely.vectorized.contains(self.land, x[land], y[land])

    return land


