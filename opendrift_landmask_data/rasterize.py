import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio import Affine
import shapely.wkb as wkb

from gshhs import GSHHS

class GSHHSMask:
    extent = [-180, 180, -90, 90]
    epsg   = '32662' # Plate Carree

def gshhs_rasterize(inwkb, outtif):
    # minimum resolution:
    # 0.269978 nm = .5 km, 1 deg = 60 nm at equator
    dnm = 0.269978
    nx = int(np.ceil(2*180/dnm))
    ny = int(np.ceil(2*90/dnm))
    x = [-180, 180]
    y = [-90, 90]

    print ('nx =', nx, 'ny =', ny)

    resx = (x[1] - x[0]) / nx
    resy = (y[1] - y[0]) / ny
    transform = Affine.translation(x[0] - resx/2, y[0]-resy/2) * Affine.scale (resx, resy)
    print ("transform = ", transform)

    with rasterio.open(outtif, 'w+',
                    driver = 'GTiff',
                    height = ny,
                    width  = nx,
                    count  = 1,
                    dtype  = 'uint8',
                    crs = 'epsg:32662', # Plate Carree
                    transform = transform) as out:

        with open(inwkb, 'rb') as fd:
            land = wkb.load(fd)

            # check out features.geometry_mask -> np.bool
            imgs = rasterize (
                    ((l, 255) for l in land),
                    out_shape = out.shape,
                    fill = 0,
                    all_touched = True,
                    transform = transform)

            print('writing mask.tif..')
            out.write (imgs, indexes = 1)


if __name__ == '__main__':
    gshhs_rasterize (GSHHS['h'], 'mask.tif')

    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt

    proj = ccrs.epsg('32662')

    plt.figure ()
    ax = plt.axes(projection=ccrs.PlateCarree())
    img = plt.imread('mask.tif')
    extent = [-180, 180, -90, 90]
    ax.imshow (img, extent = extent, transform = ccrs.PlateCarree())
    ax.coastlines()
    ax.set_global()
    plt.title("Landmask of the world based on GSHHS coastlines")

    plt.show()

