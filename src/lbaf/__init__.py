"""LBAF module"""

import os
import sys


__version__ = "0.1.0rc1"
"""lbaf module version"""

PROJECT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../../")
"""project path (with data, config, tests)"""

# pylint:disable=C0413:wrong-import-position
from lbaf.Applications.lbsLbafApplication import LBAFApplication
from lbaf.Applications.lbsVTDataExtractorApplication import VTDataExtractorApplication
# pylint:enable=C0413:wrong-import-position

# expose all applications through methods for the package

def run():
    """Run LBAF Application."""
    LBAFApplication().run()

def extract_vt_data():
    """Run VTDataExtractor Application."""
    VTDataExtractorApplication().run()

# set default behaviour of this module to run the LBAF application

if __name__ == "__main__":
    run()
