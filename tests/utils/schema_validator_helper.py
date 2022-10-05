import os
import sys
from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError

from src.lbaf.Utils.exception_handler import exc_handler
from src.lbaf.Utils.colors import green

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)


def check_and_get_schema_validator():
    """ Makes sure that SchemaValidator can be imported, and it's the latest version available.
    """
    module_name = green(f"[{os.path.splitext(os.path.split(__file__)[-1])[0]}]")

    def save_schema_validator_and_init_file(import_dir: str):
        with open(os.path.join(import_dir, "__init__.py"), 'wt') as init_file:
            init_file.write('\n')
        try:
            script_name = "JSON_data_files_validator.py"
            script_url = f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{script_name}"
            filename, http_msg = urlretrieve(script_url, os.path.join(import_dir, script_name))
            print(f"{module_name} Saved SchemaValidator to: {filename}")
        except HTTPError as err:
            sys.excepthook = exc_handler
            raise ConnectionError(f"Can not download file: {err.filename} \n"
                                  f"Server responded with code: {err.fp.code} and message: {err.fp.msg}")
        except URLError as err:
            sys.excepthook = exc_handler
            raise ConnectionError("Probably there is no internet connection")

    import_dir = os.path.join(project_path, "src", "lbaf", "imported")
    if not os.path.isfile(os.path.join(import_dir, "JSON_data_files_validator.py")):
        if not os.path.exists(import_dir):
            os.makedirs(import_dir)
            save_schema_validator_and_init_file(import_dir=import_dir)
        else:
            save_schema_validator_and_init_file(import_dir=import_dir)
