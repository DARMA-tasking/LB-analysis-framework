#
#@HEADER
###############################################################################
#
#                                 __init__.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
"""LBAF module"""

import os
import sys
import importlib.util


__version__ = "1.5.0"
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
from lbaf.Utils.lbsJSONDataFilesMaker import JSONDataFilesMaker
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
    # If using the lbaf package, don't overwrite
    if importlib.util.find_spec('lbaf'):
        JSONDataFilesValidatorLoader().run(overwrite=False)
    else:
        JSONDataFilesValidatorLoader().run(overwrite=True)
    from lbaf.imported.JSON_data_files_validator import JSONDataFilesValidator #pylint:disable=C0415:import-outside-toplevel
    JSONDataFilesValidator().main()

def vt_data_files_maker() -> int:
    """Run a JSONDataFilesMaker instance."""
    return JSONDataFilesMaker().run()

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
