# Opendrift Landmask Data

These files are simplified shapes generated from the
[GSHHS](https://www.ngdc.noaa.gov/mgg/shorelines/) dataset where connected
shapes are joined. These are useful for checking points aginst a landmask
quickly.

These are provided under the LGPL3 [LICENSE](./LICENSE) in the same way as the original work.

## Generating simplified shapes and raster-images

Run `regenerate.py` or `rasterize.py`. The resulting mask is compressed using xz. The final files are checked into the source code.

