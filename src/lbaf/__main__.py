"""LBAF module"""

import os
import sys
import importlib

# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, (os.path.dirname(__file__) + "/../"))

# Default run a LBAFApplication instance
from lbaf.Applications.LBAF_app import LBAFApplication  # pylint:disable=C0413:wrong-import-position)
LBAFApplication().run()
