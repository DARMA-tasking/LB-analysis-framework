#
#@HEADER
###############################################################################
#
#                      lbsJSONDataFilesValidatorLoader.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
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
import importlib
import os
import sys
from typing import Optional

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import Logger, get_logger
from lbaf.Utils.lbsWeb import download
# pylint:disable=C0413:wrong-import-position

CURRENT_PATH = os.path.abspath(__file__)
IMPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(CURRENT_PATH)),
    "imported")

class JSONDataFilesValidatorLoader:
    """Data Files Validator Loader application class."""

    def __init__(self):
        self.__args: dict = None
        self.__logger: Logger = get_logger()
        self.__scripts = ["JSON_data_files_validator.py", "LBDatafile_schema.py"]

    def __parse_args(self):
        """Parse arguments."""
        parser = PromptArgumentParser(allow_abbrev=False,
                                      description="Downloads the JSON_data_files_validator.py script "
                                      "from the VT repository.", prompt_default=False)
        parser.add_argument("--overwrite",
                            help="Overwrite JSON_data_files_validator.py from VT (default: True)",
                            type=bool,
                            default=True)
        self.__args = parser.parse_args()

    def __run(self, script_name, overwrite: Optional[bool] = None) -> int:
        script_url = f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{script_name}"
        script_title = script_name.replace(".py", "").replace("_"," ")

        exists = self.__is_loaded(script_name)

        # Parse command line arguments
        if overwrite is None:
            self.__parse_args()
            overwrite = self.__args.overwrite

        if overwrite:
            self.__logger.info("Overwrite JSON data files validator")

        if overwrite or not exists:
            download(script_url, IMPORT_DIR, logger=self.__logger, file_title=script_title)
            if not self.is_loaded():
                self.__logger.warning(f"{script_title} cannot be loaded")
        elif exists:
            self.__logger.info(f"{script_title} is ready to be used")
        return 0 if os.path.isfile(os.path.join(IMPORT_DIR, script_name)) else 1

    def __is_loaded(self, script_name) -> bool:
        return os.path.isfile(os.path.join(IMPORT_DIR, script_name))

    def run(self, overwrite: Optional[bool] = None) -> int:
        """Downloads the VT Data validator script named script_name from the VT repository.

        :param overwrite: None to parse arg from cli. True to overwrite the script if exists.
        :returns: False if the script cannot be loaded.
        """
        for script_name in self.__scripts:
            if self.__run(script_name, overwrite=overwrite) == 1:
                return 1
        return 0

    def is_loaded(self) -> bool:
        """Verify if the data files validator module has been downloaded.

        :returns: True if the module has been downloaded to IMPORT_DIR
        """
        for script_name in self.__scripts:
            if not self.__is_loaded(script_name):
                return False
        return True


if __name__ == "__main__":
    JSONDataFilesValidatorLoader().run()
