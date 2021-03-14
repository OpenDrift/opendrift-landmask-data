import gc
from opendrift_landmask_data import Landmask

def test_generate_landmask_static():
  l = Landmask() # make sure landmask is already generated
  assert Landmask.__mask__() is not None

  del l
  gc.collect()

  assert Landmask.__mask__() is None
  l = Landmask()

  assert Landmask.__mask__() is not None
  l2 = Landmask()

  assert l2.mask is not None
  assert l.mask is Landmask.__mask__()
  assert l2.mask is Landmask.__mask__()

def test_landmask_weakref():
  assert Landmask.__mask__() is None
  l = Landmask()
  assert Landmask.__mask__() is not None
  assert l.mask is not None

  l2 = Landmask()
  del l
  gc.collect()

  assert Landmask.__mask__() is not None
  assert l2.mask is not None

  del l2
  gc.collect()
  assert Landmask.__mask__() is None

