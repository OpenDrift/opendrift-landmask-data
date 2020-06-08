import numpy as np
import rasterio
from rasterio.features import rasterize, geometry_mask
from rasterio import Affine
import shapely.wkb as wkb

if __name__ == '__main__':
    from gshhs import get_gshhs_f
    from mask import Landmask
else:
    from .gshhs import get_gshhs_f
    from .mask import Landmask

def gshhs_rasterize(inwkb, outtif):
    dnm = Landmask.dnm
    nx = Landmask.nx
    ny = Landmask.ny
    x = [-180, 180]
    y = [-90, 90]

    print ('nx =', nx, 'ny =', ny)

    resx = float(x[1] - x[0]) / nx
    resy = float(y[1] - y[0]) / ny
    transform = Landmask.get_transform()
    print ("transform = ", transform)

    land = wkb.load(inwkb)
    with rasterio.open(outtif, 'w+',
                    driver = 'GTiff',
                    height = ny,
                    width  = nx,
                    count  = 1,
                    compress = 'packbits', # packbits are fast to read
                    dtype  = 'uint8',
                    tiled  = True,
                    blockxsize = 512,
                    blockysize = 512,
                    nbits = 1,
                    crs = 'epsg:32662', # Plate Carree
                    transform = transform) as out:


        img = rasterize (
                ((l, 255) for l in land),
                out_shape = out.shape,
                # fill = 255,
                all_touched = True,
                transform = transform)

        print('writing %s..' % outtif)
        out.write (img, indexes = 1)

    return img


def mask_rasterize(inwkb, outnp):
    dnm = Landmask.dnm
    nx = Landmask.nx
    ny = Landmask.ny
    x = [-180, 180]
    y = [-90, 90]

    print ('nx =', nx, 'ny =', ny)

    resx = float(x[1] - x[0]) / nx
    resy = float(y[1] - y[0]) / ny
    transform = Landmask.get_transform()
    print ("transform = ", transform)

    img = np.memmap(outnp, dtype = 'uint8', mode = 'w+', shape = (ny,nx))
    land = wkb.load(inwkb)

    img[:] = geometry_mask(
                land,
                invert = True,
                out_shape = (ny, nx),
                all_touched = True,
                transform = transform).astype('uint8')

    img.flush()
    print ("img shape:", img.shape)

    return img


if __name__ == '__main__':
    print ("resolution, m =", Landmask.dm)
    img = mask_rasterize(get_gshhs_f(), 'masks/mask_%.2f_nm.mm' % Landmask.dnm)
    # img = gshhs_rasterize (get_gshhs_f(), 'masks/mask_%.2f_nm.tif' % Landmask.dnm)

    # print ("plotting.. (won't work at high res)")
    # import cartopy.crs as ccrs
    # import matplotlib.pyplot as plt

    # proj = ccrs.epsg('32662')

    # plt.figure ()
    # ax = plt.axes(projection=ccrs.PlateCarree())
    # img = plt.imread('masks/mask_%.2f_nm.tif' % Landmask.dnm)
    # print (img.shape)
    # # extent = [-180, 180, -90, 90]
    # # ax.imshow (img, extent = extent, transform = ccrs.PlateCarree())
    # lons = np.linspace(-180, 180, img.shape[1])
    # lats = np.linspace(-90, 90, img.shape[0])
    # ax.contourf(lons, lats, img, transform=ccrs.PlateCarree())
    # ax.coastlines()
    # ax.set_global()
    # plt.title("Landmask of the world based on GSHHS coastlines")

    # plt.show()

