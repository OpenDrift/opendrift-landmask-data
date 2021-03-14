import gc
from . import *
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

def test_setup_landmask_retry_weakref():
  delete_mask()
  os.makedirs(tmpdir, exist_ok = True)
  m = os.stat(tmpdir).st_mode
  try:
    print("setting permissions on tmpdir to 0o000:", tmpdir)
    os.chmod(tmpdir, 0o000)

    assert Landmask.__mask__() is None

    l = Landmask()

    assert Landmask.__mask__() is not None
    assert l.mask is not None

    # second landmask should also use the same memmap as previous
    l2 = Landmask()

    assert l2.mmapf == l.mmapf
    assert l2.mask is l.mask

    # TODO: does not seem to be collected in this case!
    # del l
    # del l2
    # gc.collect()
    # assert Landmask.__mask__() is None

  finally:
    os.chmod(tmpdir, m)

