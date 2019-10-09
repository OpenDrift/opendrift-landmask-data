import numpy as np
import shapely.vectorized
import shapely.wkb as wkb

from .mask import GSHHSMask
from .gshhs import GSHHS

class Landmask:
  land = None
  mask = None

  def __init__(self):
    self.mask = np.load(GSHHSMask.maskf)
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

    assert len(x) == len(y)

    if not isinstance(x, np.ndarray):
      x = np.array(x)

    if not isinstance(y, np.ndarray):
      y = np.array(y)

    # check against landmask

