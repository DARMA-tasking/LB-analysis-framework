import os
import argparse
from typing import Optional

from lbaf import __version__, PROJECT_PATH
from lbaf.Applications.lbsApplicationBase import ApplicationBase
from lbaf.Utils.downloader import download

IMPORT_DIR = os.path.join(PROJECT_PATH, "src", "lbaf", "imported")
TARGET_SCRIPT_NAME = "JSON_data_files_validator.py"
SCRIPT_URL=f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{TARGET_SCRIPT_NAME}"
SCRIPT_TITLE = "JSON data files validator"

class DataFilesValidatorLoaderApplication(ApplicationBase):
    """Data Files Validator Loader application class."""
    def init_argument_parser(self) -> argparse.ArgumentParser:
        """Parse arguments."""
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("--overwrite",
            help="Download and overwrite JSON_data_files_validator.py from VT (default: True)",
            default=True
        )
        return parser

    def run(self, args: Optional[dict] = None) -> int:
        """Run the application.

        If args are required then this method must call the self.parse_args method.

        :param args: arguments to use or None to load from CLI
        :returns: return code. 0 if success.
        """
        self.parse_args(args)
        if self._args.overwrite:
            download(SCRIPT_URL, IMPORT_DIR, logger=self._logger, file_title=SCRIPT_TITLE)
        else:
            if not os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME)):
                self._logger.warning('The JSON data files validator has not been loaded')
            self._logger.info(
                "In case of `ModuleNotFoundError: No module named 'lbaf.imported'` set overwrite_validator to True.")
        return 0 if os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME)) else 1

    def is_loaded(self) -> bool:
        """Verify if the data files validator module has been downloaded.

        :return: True if the module has been downloaded to lbsDataFilesValidatorLoaderApplication.IMPORT_DIR
        """
        return os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME))
