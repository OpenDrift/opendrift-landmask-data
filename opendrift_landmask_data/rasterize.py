import numpy as np
import rasterio
from rasterio.features import rasterize, geometry_mask
from rasterio import Affine
import shapely.wkb as wkb

if __name__ == '__main__':
    from gshhs import GSHHS
    from mask import GSHHSMask
else:
    from .gshhs import GSHHS
    from .mask import GSHHSMask

def gshhs_rasterize(inwkb, outtif):
    dnm = GSHHSMask.dnm
    nx = GSHHSMask.nx
    ny = GSHHSMask.ny
    x = [-180, 180]
    y = [-90, 90]

    print ('nx =', nx, 'ny =', ny)

    resx = (x[1] - x[0]) / nx
    resy = (y[1] - y[0]) / ny
    transform = Affine.translation(x[0] - resx/2, y[0]-resy/2) * Affine.scale (resx, resy)
    print ("transform = ", transform)

    with open(inwkb, 'rb') as fd:
        land = wkb.load(fd)

        with rasterio.open(outtif, 'w+',
                        driver = 'GTiff',
                        height = ny,
                        width  = nx,
                        count  = 1,
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
    dnm = GSHHSMask.dnm
    nx = GSHHSMask.nx
    ny = GSHHSMask.nx
    x = [-180, 180]
    y = [-90, 90]

    print ('nx =', nx, 'ny =', ny)

    resx = (x[1] - x[0]) / nx
    resy = (y[1] - y[0]) / ny
    transform = Affine.translation(x[0] - resx/2, y[0]-resy/2) * Affine.scale (resx, resy)
    # transform = rasterio.transform.IDENTITY
    print ("transform = ", transform)

    with open(inwkb, 'rb') as fd:
        land = wkb.load(fd)

        # check out features.geometry_mask -> np.bool
        img = geometry_mask (
                land,
                invert = True,
                out_shape = (ny, nx),
                all_touched = True,
                transform = transform)

    np.save (outnp, img, allow_pickle=False)
    return img


if __name__ == '__main__':
    print ("resolution, m =", GSHHSMask.dm)
    # img = mask_rasterize(GSHHS['c'], 'masks/mask_%.2f_nm' % GSHHSMask.dnm)
    img = gshhs_rasterize (GSHHS['f'], 'masks/mask_%.2f_nm.tif' % GSHHSMask.dnm)

    # print ("plotting.. (won't work at high res)")
    # import cartopy.crs as ccrs
    # import matplotlib.pyplot as plt

    # proj = ccrs.epsg('32662')

    # plt.figure ()
    # ax = plt.axes(projection=ccrs.PlateCarree())
    # img = plt.imread('masks/mask_%.2f_nm.tif' % GSHHSMask.dnm)
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

