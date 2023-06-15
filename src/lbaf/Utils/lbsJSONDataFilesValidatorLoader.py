import os
import argparse
from typing import Optional

from lbaf import __version__, PROJECT_PATH
from lbaf.Utils.lbsRunnerBase import RunnerBase
from lbaf.Utils.web import download

IMPORT_DIR = os.path.join(PROJECT_PATH, "src", "lbaf", "imported")
TARGET_SCRIPT_NAME = "JSON_data_files_validator.py"
SCRIPT_URL=f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{TARGET_SCRIPT_NAME}"
SCRIPT_TITLE = "JSON data files validator"

class JSONDataFilesValidatorLoader(RunnerBase):
    """Data Files Validator Loader application class."""

    def init_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("--overwrite",
            help="Overwrite JSON_data_files_validator.py from VT (default: True)",
            type=bool,
            default=True
        )
        return parser

    def run(self, args: Optional[dict] = None) -> int:
        self.load_args(args)
        self._logger.info("loaded args")
        if self._args.overwrite:
            self._logger.info("Overwrite JSON data files validator")

        if self._args.overwrite or not os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME)):
            download(SCRIPT_URL, IMPORT_DIR, logger=self._logger, file_title=SCRIPT_TITLE)
            if not self.is_loaded():
                self._logger.warning('The JSON data files validator cannot be loaded')
        return 0 if os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME)) else 1

    def is_loaded(self) -> bool:
        """Verify if the data files validator module has been downloaded.

        :returns: True if the module has been downloaded to lbsDataFilesValidatorLoaderApplication.IMPORT_DIR
        """
        return os.path.isfile(os.path.join(IMPORT_DIR, TARGET_SCRIPT_NAME))

if __name__ == "__main__":
    JSONDataFilesValidatorLoader().run()
