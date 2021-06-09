import numpy as np
import shapely
import shapely.vectorized
import shapely.wkb as wkb
from shapely.geometry import box, MultiPolygon
import tempfile
import os
import os.path
import logging
logger = logging.getLogger(__name__)
import threading
import weakref


class Landmask:
    extent = [-180, 180, -90, 90]
    epsg = '32662'  # Plate Carree

    ## minimum resolution:
    ## 0.269978 nm = .5 km, 1 deg <= 60 nm (at equator)
    nx = 2 * 180 * 60 * 4
    ny = 2 * 90 * 60 * 4
    dnm = 1. / 4.
    dm = dnm * 1852.
    dx = float(extent[1] - extent[0]) / nx
    dy = float(extent[3] - extent[2]) / ny

    polys = None
    land = None
    __mask__ = lambda: None  # class weakreffed mask
    mask = None  # instance ref to mask
    transform = None
    invtransform = None

    tmpdir = os.path.join(tempfile.gettempdir(), 'landmask')
    DEFAULT_MMAPF = os.path.join(tmpdir, 'mask.dat')
    mmapf = os.path.join(tmpdir, 'mask.dat')
    lockf = os.path.join(tmpdir, '.mask.dat.lock')

    tmpmask = None

    __concurrency_delay__ = 0
    __concurrency_abort__ = False
    __no_retry__ = False
    __fake_32_bit__ = False
    generation_lock = threading.Lock()

    @staticmethod
    def get_mask():
        from pkg_resources import resource_stream
        masktif = os.path.join('masks', 'mask_%.2f_nm.mm.xz' % Landmask.dnm)
        return resource_stream(__name__, masktif)

    @staticmethod
    def get_transform():
        from affine import Affine
        x = [-180, 180]
        y = [-90, 90]
        resx = float(x[1] - x[0]) / Landmask.nx
        resy = float(y[1] - y[0]) / Landmask.ny
        return Affine.translation(x[0] - resx / 2,
                                  y[0] - resy / 2) * Affine.scale(resx, resy)

    @staticmethod
    def get_inverse_transform():
        return ~Landmask.get_transform()

    def __32_bit__(self):
        import sys
        return sys.maxsize <= 2**32 or self.__fake_32_bit__

    def __mask_exists__(self):
        return os.path.exists(self.mmapf)

    def __check_permissions__(self):
        if self.__mask_exists__():
            try:
                if not os.stat(self.mmapf).st_mode & 0o444 == 0o444:
                    logger.warning(
                        "permissions too restrictive on landmask, trying to relax."
                    )
                    os.chmod(self.mmapf, 0o444)

                if os.path.exists(self.lockf) and not os.stat(
                        self.lockf).st_mode & 0o777 == 0o777:
                    logger.warning(
                        "permissions too restrictive on landmask lock file, trying to relax."
                    )
                    os.chmod(self.lockf, 0o777)

            except:
                logger.exception(
                    "could not verify read permissions for group and others on landmask."
                )

    def __generate_impl__(self, temporary=False):
        if not temporary and self.__mask_exists__():
            logger.warning("mask already exists, aborting generation..")
            return

        try:
            fd = tempfile.NamedTemporaryFile(delete=temporary)
            if temporary:
                mask = fd.name
                Landmask.tmpmask = fd  # keep handle around and delete on destruct
            else:
                mask = self.DEFAULT_MMAPF

            logger.info("decompressing memmap landmask to %s.." % mask)

            import lzma, shutil
            with lzma.open(self.get_mask(), 'rb') as zmask:
                shutil.copyfileobj(zmask, fd)
            fd.flush()

            if self.__concurrency_delay__ > 0:
                logger.warn("concurrency testing: sleeping: %.2fs" %
                            self.__concurrency_delay__)
                import time
                time.sleep(self.__concurrency_delay__)

            if self.__concurrency_abort__:
                logger.error("concurrency testing: landmask aborted (planned)")
                fd.close()
                os.unlink(fd.name)

            else:
                if not temporary:
                    fd.close()
                    os.rename(fd.name, mask)

                try:
                    os.chmod(mask, 0o444)
                except:
                    logger.exception(
                        "could not set read permissions for group and others on landmask."
                    )

                Landmask.mmapf = mask
                logger.info("landmask generated")

        except:
            logger.exception("failed to generate landmask")
            raise

    def __generate__(self):
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

        if self.generation_lock.acquire(blocking=False):
            try:
                import fcntl

                with open(self.lockf, 'w') as fd:
                    try:
                        os.chmod(self.lockf, 0o777)
                    except:
                        logger.warning("could not permissions for lock file.")

                    # try to get non-blocking lock, if fail, another process is presumably generating the
                    # landmask. so we wait.
                    try:
                        logger.info("locking landmask for generation..")
                        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

                        # we got the lock, now generate mask
                        self.__generate_impl__()

                    except OSError:
                        # file already locked
                        logger.warn(
                            "landmask is being generated in another process, waiting for it to complete.."
                        )

                        fcntl.lockf(fd, fcntl.LOCK_EX)  # blocks

                        logger.info(
                            "landmask generation done in another process, attempting to load.."
                        )

                        if not self.__mask_exists__():
                            logger.warn(
                                "landmask generation failed in other process (perhaps it was killed), re-trying.."
                            )

                            # we already have lock
                            self.__generate_impl__()

            except ImportError:
                logger.error(
                    "fcntl not available on this platform, concurrent generations of landmask (different threads or processes) might cause failing landmask generation. Make sure only one instance of landmask is running on the system the first time."
                )
                self.__generate_impl__()

            except:
                logger.exception(
                    "failed to generate landmask: re-trying to create landmask in temporary location."
                )
                if not self.__no_retry__:
                    self.__generate_impl__(True)
                else:
                    logger.error("retry disabled for testing.")
                    raise

            finally:
                self.generation_lock.release()

        else:
            logger.warn(
                "landmask is being generated in another thread, waiting for it to complete.."
            )
            self.generation_lock.acquire(True)
            self.generation_lock.release()
            logger.info(
                "landmask generation done in another thread, attempting to load.."
            )

    def __memmap_mask__(self):
        self.mask = Landmask.__mask__()
        if self.mask is None:
            try:
                logger.debug("memmapping mask..")
                Landmask.generation_lock.acquire(True)
                if not self.__32_bit__():
                    self.mask = np.memmap(self.mmapf,
                                          dtype='uint8',
                                          mode='r',
                                          shape=(Landmask.ny, Landmask.nx))
                else:
                    logger.warning(
                        "cannot memorymap mask on 32-bit system, loading into memory.."
                    )
                    with open(self.mmapf, 'rb') as fd:
                        logger.debug('reading into buffer..')
                        buffer = fd.read()
                        logger.debug('constructing array..')
                        self.mask = np.ndarray.__new__(np.ndarray,
                                                       buffer=buffer,
                                                       dtype='uint8',
                                                       shape=(Landmask.ny,
                                                              Landmask.nx))

                Landmask.__mask__ = weakref.ref(self.mask)

                # XXX: It seems that when the mask is generated in a
                # temp-location because of failing normal generation, the
                # weakref is not collected. At least not immediately.
                Landmask.generation_lock.release()
            except:
                Landmask.generation_lock.release()
                raise
        else:
            logger.debug("mask already memmapped")

    def __open_mask__(self):
        if self.__retry_delete__:
            logger.warning("testing: deleting generated mmapf before opening")
            os.unlink(self.mmapf)

        try:
            self.__memmap_mask__()
        except Exception as ex:
            logger.error(
                "could not open landmask, re-trying to generate to temporary location: %s"
                % ex)
            if not self.__no_retry__:
                self.__generate_impl__(True)
                self.__memmap_mask__()
            else:
                raise

    def __init__(self,
                 extent=None,
                 skippoly=False,
                 __concurrency_delay__=0,
                 __concurrency_abort__=False,
                 __no_retry__=False,
                 __retry_delete__=False,
                 __fake_32_bit__=False):
        """
        Initialize landmask from generated GeoTIFF

        Args:

          extent (array): [xmin, ymin, xmax, ymax]
          skippoly (bool): do not load polygons

          __concurrency_delay__: internally used for race condition testing, do not use.
          __concurrency_abort__: internally used for race condition testing, do not use.
          __no_retry__: internally used for mask generation testing, do not use.
          __retry_delete__: internally used for mask generation testing, do not use.
          __fake_32_bit__: internally used for mask generation testing, do not use.
        """
        self.extent = extent
        self.transform = self.get_transform()
        self.invtransform = self.get_inverse_transform()
        self.skippoly = skippoly
        self.__concurrency_delay__ = __concurrency_delay__
        self.__concurrency_abort__ = __concurrency_abort__
        self.__no_retry__ = __no_retry__
        self.__retry_delete__ = __retry_delete__
        self.__fake_32_bit__ = __fake_32_bit__

        self.__check_permissions__()

        if not self.__mask_exists__():
            self.__generate__()

        self.__open_mask__()

        if not skippoly:
            from .gshhs import get_gshhs_f
            with get_gshhs_f() as fd:
                self.land = wkb.load(fd)

            if extent:
                self.extent = box(*extent)
                self.extent = shapely.prepared.prep(self.extent)

                # polygons
                self.land = MultiPolygon(
                    [l for l in self.land.geoms if self.extent.intersects(l)])

            self.polys = self.land
            self.land = shapely.prepared.prep(self.land)

    def contains(self, x, y, skippoly=None, checkextent=True):
        """
        Check if coordinates x, y are on land

        Args:
          x (scalar or array, deg): longitude

          y (scalar or array, deg): latitude

          skippoly (bool): skip check against polygons, default False unless constructed with True.

          checkextent (bool): check if points are within extent of landmask, default True

        Returns:

          array of bools same length as x and y
        """
        if skippoly is not None:
            assert not (
                not skippoly and self.skippoly
            ), "cannot check against polygons when not constructed with polygons"
        else:
            skippoly = self.skippoly

        if not isinstance(x, np.ndarray):
            x = np.array(x, ndmin=1, dtype=np.float32)

        if not isinstance(y, np.ndarray):
            y = np.array(y, ndmin=1, dtype=np.float32)

        xm, ym = self.invtransform * (x, y)

        xm = xm.astype(np.int32)
        ym = ym.astype(np.int32)
        xm[xm == self.nx] = self.nx - 1
        ym[ym == self.ny] = self.ny - 1

        land = self.mask[ym, xm] == 1

        # checking against polygons
        if not skippoly and len(x[land]) > 0:

            if checkextent and self.extent is not None:
                assert np.all(
                    shapely.vectorized.contains(
                        self.extent, x[land],
                        y[land])), "Points are not inside extent."

            land[land] = shapely.vectorized.contains(self.land, x[land],
                                                     y[land])

        return land
