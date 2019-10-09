import os.path

mask = os.path.join(os.path.dirname(__file__), 'masks') + os.path.sep

class GSHHSMask:
    extent = [-180, 180, -90, 90]
    epsg   = '32662' # Plate Carree

    ## minimum resolution:
    ## 0.269978 nm = .5 km, 1 deg <= 60 nm (at equator)
    # dnm    = 0.269978 # nm
    dnm    = 0.1
    dm     = dnm * 1852.
    dx     = 2*180/dnm
    dy     = 2*90/dnm
    maskf  = os.path.join (mask, 'mask_%.2f_nm.npy' % dnm)

