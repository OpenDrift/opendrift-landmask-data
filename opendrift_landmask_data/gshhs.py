import os.path

shapes = os.path.join(os.path.dirname(__file__), 'shapes') + os.path.sep


def get_gshhs_f():
    from pkg_resources import resource_stream
    f = os.path.join(
        'shapes',
        'gshhs_%s_-180.000000E-90.000000N180.000000E90.000000N.wkb' % 'f')
    return resource_stream(__name__, f)
