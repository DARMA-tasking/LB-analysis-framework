"""Downloads the latest version of the JSON data files validator to the src/lbaf/imported directory"""
import os
import sys

from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError

from lbaf.Utils.common import project_path
from lbaf.Utils.logging import get_logger
from lbaf.Utils.exception_handler import exc_handler

TARGET_DIR = os.path.join(project_path(), "src", "lbaf", "imported")
TARGET_SCRIPT_NAME = "JSON_data_files_validator.py"
SOURCE_SCRIPT_URL=f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{TARGET_SCRIPT_NAME}"

def _save_schema_validator_and_init_file():
    """Downloads the JSON data files validator module to the lbaf/imported directory

    :raises ConnectionError: on connection error
    :raises ConnectionError: on HTTP response error
    :raises ConnectionError: on invalid content type and if no previous download is available
    """

    # Create src/lbaf/imported directory if not exist
    if not os.path.isdir(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    logger = get_logger()

    # create empty __init__.py file
    with open(os.path.join(TARGET_DIR, "__init__.py"), "wt", encoding="utf-8"):
        pass
    # then download the SchemaValidator for vt files
    try:
        logger.info(f"Retrieve the JSON data files validator at {SOURCE_SCRIPT_URL}")
        tmp_filename, http_message = urlretrieve(SOURCE_SCRIPT_URL, os.path.join(TARGET_DIR, '~' + TARGET_SCRIPT_NAME))
        filename = os.path.join(TARGET_DIR, TARGET_SCRIPT_NAME)
        content_type = http_message.get_content_type()
        # validate content type for script that has been retrieved
        if content_type == 'text/plain':
            os.rename(tmp_filename, filename)
            logger.info(f"Saved JSON data files validator to: {filename}")
        else:
            os.remove(tmp_filename)
            if os.path.isfile(filename):
                logger.error(
                    f"Unexpected Content-Type ({content_type}) for JSON data files validator file."
                    " Using last valid JSON data files validator: {filename}"
                )
            else:
                raise ConnectionError(
                    f"Unexpected Content-Type `{content_type}` for schema validator" +
                    "downloaded from {script_url}\n"
                )
    except HTTPError as err:
        sys.excepthook = exc_handler
        raise ConnectionError(f"Can not download file: {err.filename} \n"
                                f"Server responded with code: {err.fp.code} and message: {err.fp.msg}") from err
    except URLError as err:
        sys.excepthook = exc_handler
        raise ConnectionError("Probably there is no internet connection") from err

def load(overwrite_validator: bool = True):
    """Makes sure that JSON data files validator can be imported, and it's the latest version available.

    :param overwrite_validator: set true to download the script, defaults to True
    :type overwrite_validator: bool, optional
    """

    logger = get_logger()
    if overwrite_validator:
        _save_schema_validator_and_init_file()
    else:
        if not is_loaded():
            logger.warning('The JSON data files validator has not been loaded')
        logger.info(
            "In case of `ModuleNotFoundError: No module named 'lbaf.imported'` set overwrite_validator to True.")

def is_loaded():
    """Verify if the module is loaded

    :return: True if the script exists in the target location otherwise False
    :rtype: bool
    """

    import_dir = os.path.join(project_path(), "src", "lbaf", "imported")
    return os.path.isfile(os.path.join(import_dir, TARGET_SCRIPT_NAME))
