import os.path
import math

mask = os.path.join(os.path.dirname(__file__), 'masks') + os.path.sep

class GSHHSMask:
  extent = [-180, 180, -90, 90]
  epsg   = '32662' # Plate Carree

  ## minimum resolution:
  ## 0.269978 nm = .5 km, 1 deg <= 60 nm (at equator)
  # dnm    = 0.269978 # nm
  dnm    = 0.26
  dm     = dnm * 1852.
  nx     = int(math.ceil(2*180*60/dnm))
  ny     = int(math.ceil(2*90*60/dnm))
  dx     = (extent[1] - extent[0])/nx
  dy     = (extent[3] - extent[2])/ny
  maskf  = os.path.join (mask, 'mask_%.2f_nm.npy' % dnm)

  def grid(self):
    import numpy as np
    x = np.arange(self.extent[0], self.extent[1], self.dx)
