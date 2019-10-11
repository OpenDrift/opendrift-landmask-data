import numpy as np
import shapely
import shapely.vectorized
import shapely.wkb as wkb
import shapely.strtree
from shapely.ops import unary_union
from shapely.geometry import box, MultiPolygon, Polygon
import rasterio
import cartopy

from .mask import GSHHSMask
from .gshhs import GSHHS

class Landmask:
  land = None
  mask = None
  extent = None

  def __init__(self, extent = None):
    """
    Initialize landmask from generated GeoTIFF

    Args:

      extent (array): [xmin, ymin, xmax, ymax]
    """
    self.extent = extent

    # self.mask = np.load(GSHHSMask.masknpy, mmap_mode = 'r')
    with rasterio.open(GSHHSMask.masktif, 'r') as src:
      self.mask = src.read(1)
      print (self.mask.shape)
      print (self.mask)

    # tree = shapely.strtree.STRtree(self.land.geoms)
    # self.extent = box(*extent)
    # lands = MultiPolygon(tree.query(self.extent))
    # self.extent = shapely.prepared.prep(box(*self.extent))
    # self.land = shapely.prepared.prep(lands)

    ### CARTOPY
    #reader = cartopy.feature.GSHHSFeature(scale = 'i', level = 1)
    #print ("preparing polygons..:", extent)
    ##cartopy uses interleved extent
    #extentint = [extent[0], extent[2], extent[1], extent[3]] if extent else None
    #self.land = [shapely.prepared.prep(shp)
    #             for shp in reader.intersecting_geometries(extentint)]
    #print ("cartopy polys:", len(self.land))
    #print ("done.")
    ######

    print ("loading prepared polygons..")
    with open(GSHHS['f'], 'rb') as fd:
      self.land = wkb.load(fd)
    print ("preparing polygons..:", extent)
    if extent is not None:
      ex = box(*extent)
      print ("polys before:", len(self.land.geoms))

      self.land = MultiPolygon([l for l in self.land.geoms if ex.intersects(l)])
      print ("polys after:", len(self.land.geoms))
    self.land = shapely.prepared.prep(self.land)

    # warmup
    self.contains([15], [65])

  # def prepare_polygon(self, p):
  #   if isinstance(p, MultiPolygon):
  #     return shapely.prepared.prep(
  #               MultiPolygon((Polygon(pp.exterior) for pp in p.geoms))
  #            )
  #   elif isinstance(p, Polygon):
  #     return shapely.prepared.prep(p.exterior)

  # @jit(nopython=True)
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
      x = np.array(x, ndmin = 1)

    if not isinstance(y, np.ndarray):
      y = np.array(y, ndmin = 1)

    assert len(x) == len(y)

    xm = (x - (-180)) / (180*2) * GSHHSMask.nx - GSHHSMask.dx
    ym = (y - (-90)) / (90*2)   * GSHHSMask.ny - GSHHSMask.dy

    # print (GSHHSMask.nx, GSHHSMask.ny, self.mask.shape)

    # print ("checking:", len(x), ":", x, y, " -> ", xm, ym)
    land = self.mask[ym.astype(np.int32), xm.astype(np.int32)] == 1
    # print ("land:", land.astype(np.uint8))

    # checking against polygons
    # if self.extent is not None:
    #   assert np.all(shapely.vectorized.contains(self.extent, x[land], y[land])), "Points are not inside extent."

    print ("checking against polys:", len(x))
    if len(x) > 0:
      land[land] = self.poly_check(x[land], y[land])
    print ("checked against poly.")

    return land

  def poly_check(self, x, y):
    land = shapely.vectorized.contains(self.land, x, y)
    # land = np.zeros(len(x), dtype = np.bool)

    # for shp in self.land:
    #   if np.all(land): break

    #   land = np.logical_or(land, shapely.vectorized.contains(shp, x, y))

    return land




