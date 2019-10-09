import pytest

from opendrift_landmask_data.contains import Landmask

def test_setup_landmask(benchmark):
  l = benchmark(Landmask)

def test_landmask_contains(benchmark):
  l = Landmask()

