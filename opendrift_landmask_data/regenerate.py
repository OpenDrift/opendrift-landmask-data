import os
import os.path
import cartopy
from shapely.ops import unary_union
import shapely.wkb


def generate(resolution):
    reader = cartopy.feature.GSHHSFeature(scale=resolution, level=2)
    land_geom = unary_union(list(reader.geometries()))

    xmin, ymin = -180, -90
    xmax, ymax = 180, 90
    if not os.path.exists("shapes"): os.makedirs("shapes")
    cachef = os.path.join(
        "shapes", "%s_%s_%3.6fE%3.6fN%3.6fE%3.6fN.wkb" %
        ("gshhs", resolution, xmin, ymin, xmax, ymax))

    print("saving cache to: %s.." % cachef)

    with open(cachef, 'wb') as fd:
        fd.write(shapely.wkb.dumps(land_geom))


print("pre generating cache for sources and resolutions for entire world")
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=8) as executor:
    resolutions = ['c', 'l', 'i', 'h', 'f']
    for resolution in resolutions:
        print(
            "preparing cache for %s, resolution '%s'.. this will take a while"
            % ("gshhs", resolution))
        executor.submit(generate, resolution)
print("done.")
