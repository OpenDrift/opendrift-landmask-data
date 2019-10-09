import pytest
import opendrift_landmask_data as old
from . import *
import shapely
import shapely.vectorized
from shapely.geometry import Point
import shapely.wkb as wkb
import numpy as np

def test_load():
  with open(old.GSHHS['c'], 'rb') as fd:
    land = wkb.load (fd)

def test_simple_contains():
  with open(old.GSHHS['c'], 'rb') as fd:
    land = wkb.load (fd)

  onland = (np.array([15.]), np.array([65.6]))
  onocean = (np.array([5.]), np.array([65.6]))

  assert land.contains (Point(onland[0], onland[1]))
  assert not land.contains(Point(*onocean))

def test_prep_vectorized_coarse(benchmark, coarse):
  prep = shapely.prepared.prep(coarse)
  xx, yy = np.mgrid[-180:180,-90:90] # 64800 points

  contains = benchmark(shapely.vectorized.contains, prep, xx.ravel(), yy.ravel())
  assert np.any(contains)

def test_prep_vectorized_high(benchmark, high):
  prep = shapely.prepared.prep(high)
  xx, yy = np.mgrid[-180:180,-90:90] # 64800 points
  xx = xx.astype('float64').ravel()
  yy = yy.astype('float64').ravel()

  contains = benchmark(shapely.vectorized.contains, prep, xx, yy)
  assert np.any(contains)

