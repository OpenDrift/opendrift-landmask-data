import pytest
import opendrift_landmask_data as old
import shapely.wkb as wkb

@pytest.fixture
def coarse():
  with open(old.GSHHS['c'], 'rb') as fd:
    land = wkb.load (fd)
  return land

@pytest.fixture
def high():
  with open(old.GSHHS['h'], 'rb') as fd:
    land = wkb.load (fd)
  return land

