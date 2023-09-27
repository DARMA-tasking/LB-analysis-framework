import importlib
import os
import sys
from typing import Optional

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH, __version__
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import Logger, get_logger
from lbaf.Utils.lbsWeb import download
# pylint:disable=C0413:wrong-import-position

IMPORT_DIR = os.path.join(PROJECT_PATH, "src", "lbaf", "imported")
TARGET_SCRIPT_NAME = "JSON_data_files_validator.py"
SCRIPT_URL = f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{TARGET_SCRIPT_NAME}"
SCRIPT_TITLE = "JSON data files validator"


class JSONDataFilesValidatorLoader:
    """Data Files Validator Loader application class."""

    def __init__(self):
        self.__args: dict = None
        self.__logger: Logger = get_logger()

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

    def run(self, overwrite: Optional[bool] = None) -> int:
        """Downloads the VT Data validator script named self.TARGET_SCRIPT_NAME from the VT repository.

        :param overwrite: None to parse arg from cli. True to overwrite the script if exists.
        :returns: False if the script cannot be loaded.
        """
        exists = self.is_loaded()
        # Parse command line arguments
        if overwrite is None:
            self.__parse_args()
            overwrite = self.__args.overwrite

        if overwrite:
            self.__logger.info("Overwrite JSON data files validator")

        if overwrite or not exists:
            download(SCRIPT_URL, IMPORT_DIR, logger=self.__logger, file_title=SCRIPT_TITLE)
            if not self.is_loaded():
                self.__logger.warning("The JSON data files validator cannot be loaded")
        elif exists:
            self.__logger.info("The JSON data files is ready to be used")
        return 0 if os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME)) else 1

    def is_loaded(self) -> bool:
        """Verify if the data files validator module has been downloaded.

        :returns: True if the module has been downloaded to lbsDataFilesValidatorLoaderApplication.IMPORT_DIR
        """
        return os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME))


if __name__ == "__main__":
    JSONDataFilesValidatorLoader().run()
