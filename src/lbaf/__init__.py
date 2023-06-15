"""LBAF module"""

import os
import sys


__version__ = "0.1.0rc1"
"""lbaf module version"""

PROJECT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../../")
"""project path (with data, config, tests)"""

# pylint:disable=C0413:wrong-import-position
from lbaf.Applications.lbsLBAFApplication import LBAFApplication
from lbaf.Utils.lbsVTDataExtractor import VTDataExtractorRunner
from lbaf.Utils.lbsVTDataFilesValidatorLoader import VTDataFilesValidatorLoader
from lbaf.Applications.lbsMoveCountsViewer import MoveCountsViewer
from lbaf.Utils.lbsCsv2JsonDataConverter import Csv2JsonConverter
# pylint:enable=C0413:wrong-import-position

# expose all runnable applications and utility scripts
# through methods from the top of the lbaf package (this file)
# these methods correspond to console commands as defined in setup.cfg
def run() -> int:
    """Run a LBAFApplication instance."""
    return LBAFApplication().run()

def vt_data_extractor() -> int:
    """Run a VTDataExtractorRunner instance."""
    return VTDataExtractorRunner().run()

def vt_data_validator_loader() -> int:
    """Run a VTDataFilesValidatorLoader instance."""
    return VTDataFilesValidatorLoader().run()

def move_counts_viewer() -> int:
    """Run a MoveCountsViewer instance."""
    return MoveCountsViewer().run()

def vt_data_converter() -> int:
    """Run a Csv2JsonConverter instance."""
    return Csv2JsonConverter().run()

# set default behaviour if calling this module to run the LBAF application
if __name__ == "__main__":
    run()
