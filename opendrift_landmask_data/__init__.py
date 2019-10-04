import os.path

shapes = os.path.join(os.path.dirname(__file__), 'shapes') + os.path.sep
GSHHS = [ os.path.join (shapes, 'gshhs_%s_-180.000000E-90.000000N180.000000E90.000000N.wkb' % r) for r in ['c', 'l', 'i', 'h', 'f'] ]

