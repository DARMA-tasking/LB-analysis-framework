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
from lbaf.Applications.lbsDataFilesValidatorLoaderApplication import DataFilesValidatorLoaderApplication

# pylint:enable=C0413:wrong-import-position

# expose all applications through methods for the package defined in setup.cfg
def run() -> int:
    """Run LBAFApplication instance."""
    return LBAFApplication().run()

def extract_vt_data() -> int:
    """Run a VTDataExtractorApplication instance."""
    return VTDataExtractorApplication().run()

def load_data_files_validator(overwrite: bool = True) -> int:
    """Run a DataFilesValidatorLoaderApplication instance."""
    return (DataFilesValidatorLoaderApplication()
        .parse_args({ "overwrite": overwrite })
        .run())

# set default behaviour if calling this module to run the LBAF application
if __name__ == "__main__":
    run()
