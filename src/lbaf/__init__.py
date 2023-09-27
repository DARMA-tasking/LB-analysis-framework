"""LBAF module"""

import os
import sys
import importlib


__version__ = "1.0.0"
"""lbaf module version"""

PROJECT_PATH = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
"""project path (with data, config, tests)"""

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2]))
from lbaf.Applications.LBAF_app import LBAFApplication
from lbaf.Utils.lbsVTDataExtractor import VTDataExtractorRunner
from lbaf.Utils.lbsJSONDataFilesValidatorLoader import JSONDataFilesValidatorLoader
from lbaf.Applications.MoveCountsViewer import MoveCountsViewer
from lbaf.Utils.lbsCsv2JsonDataConverter import Csv2JsonConverter
from lbaf.Utils.lbsDataStatFilesUpdater import DataStatFilesUpdater
# pylint:enable=C0413:wrong-import-position

# lbaf functions to expose as lbaf package console commands (see setup.cfg)
def run() -> int:
    """Run a LBAFApplication instance."""
    return LBAFApplication().run()

def vt_data_extractor() -> int:
    """Run a VTDataExtractorRunner instance."""
    return VTDataExtractorRunner().run()

def vt_data_files_validator_loader() -> int:
    """Run a JSONDataFilesValidatorLoader instance."""
    return JSONDataFilesValidatorLoader().run()

def vt_data_files_validator():
    """Run vt_data_validator instance."""
    JSONDataFilesValidatorLoader().run(overwrite=True)
    from lbaf.imported.JSON_data_files_validator import JSONDataFilesValidator #pylint:disable=C0415:import-outside-toplevel
    JSONDataFilesValidator().main()

def move_counts_viewer():
    """Run a MoveCountsViewer instance."""
    return MoveCountsViewer().run()

def csv_2_json_converter() -> int:
    """Run a Csv2JsonConverter instance."""
    return Csv2JsonConverter().run()

def vt_data_stat_files_updater() -> int:
    """Run a DataStatFilesUpdater instance."""
    return DataStatFilesUpdater().run()

# set default behaviour if calling this module to run the LBAF application
if __name__ == "__main__":
    run()
