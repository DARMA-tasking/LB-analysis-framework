"""Downloads the latest version of the Schema Validator to the src/lbaf/imported directory"""
import os
import sys

from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError

from ..Utils.common import project_dir
from ..Utils.logger import logger
from ..Utils.exception_handler import exc_handler


def _save_schema_validator_and_init_file():
    """Initialize src/lbaf/import directory and downloads the Schema Validator script into it"""

    # Create src/lbaf/imported directory if not exist
    import_dir = os.path.join(project_dir(), "src", "lbaf", "imported")
    if not os.path.isdir(import_dir):
        os.makedirs(import_dir)

    # create empty __init__.py file
    with open(os.path.join(import_dir, "__init__.py"), 'wt', encoding='utf-8'):
        pass
    # then download the SchemaValidator for vt files
    try:
        script_name = "JSON_data_files_validator.py"
        script_url = f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{script_name}"
        logger().info(f"Retrieve SchemaValidator at {script_url}")
        tmp_filename, http_message = urlretrieve(script_url, os.path.join(import_dir, '~' + script_name))
        filename = os.path.join(import_dir, script_name)
        content_type = http_message.get_content_type()
        # validate content type for script that has been retrieved
        if content_type == 'text/plain':
            os.rename(tmp_filename, filename)
            logger().info(f"Saved SchemaValidator to: {filename}")
        else:
            os.remove(tmp_filename)
            if os.path.isfile(filename):
                logger().error(
                    f"Unexpected Content-Type ({content_type}) for SchemaValidator file."
                    " Using last valid SchemaValidator: {filename}"
                )
            else:
                raise ConnectionError(
                    f'Unexpected Content-Type `{content_type}` for schema validator' +
                    'downloaded from {script_url}\n'
                )
    except HTTPError as err:
        sys.excepthook = exc_handler
        raise ConnectionError(f"Can not download file: {err.filename} \n"
                                f"Server responded with code: {err.fp.code} and message: {err.fp.msg}") from err
    except URLError as err:
        sys.excepthook = exc_handler
        raise ConnectionError("Probably there is no internet connection") from err

def check_and_get_schema_validator(overwrite_validator: bool = True):
    """Makes sure that SchemaValidator can be imported, and it's the latest version available."""
    if overwrite_validator:
        _save_schema_validator_and_init_file()
    else:
        logger().info(
            "In case of `ModuleNotFoundError: No module named 'lbaf.imported'` set overwrite_validator to True.")
