import gc
from . import *
from opendrift_landmask_data import Landmask
import numpy as np

def test_load_32bit():
  Landmask.__fake_32_bit__ = True

  l = Landmask()
  assert l.__32_bit__() == True
  Landmask.__fake_32_bit__ = False

  onland = (np.array([15.]), np.array([65.6]))
  assert l.contains(onland[0], onland[1])

  onland = (np.array([10.]), np.array([60.0]))
  assert l.contains(onland[0], onland[1])

  onocean = (np.array([5.]), np.array([65.6]))
  assert not l.contains(onocean[0], onocean[1])

  l.contains([180], [90])
  l.contains([-180], [90])
  l.contains([180], [-90])

