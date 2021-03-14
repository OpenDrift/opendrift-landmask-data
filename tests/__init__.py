import pytest
import tempfile
import os

tmpdir = os.path.join (tempfile.gettempdir(), 'landmask')
mmapf = os.path.join(tmpdir, 'mask.dat')

def delete_mask():
  print("deleting mask:", mmapf)
  if os.path.exists(mmapf):
    os.unlink(mmapf)
