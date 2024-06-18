"""
Utility to create and export a data file supporting shared blocks
To call this script either call package console script `lbaf-json-dataset-maker`
or call python src/lbaf/Utils/lbsJSONDatasetMaker.py
"""
import importlib
import importlib.util
import json
import os
import sys
from typing import Optional, List
from ..Model.lbsObject import Object

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger, Logger
# pylint:disable=C0413:wrong-import-position

try:
    import brotli
    HAS_BROTLI = True
except ImportError as e:
    print(f"Brotli was not imported: {e}")
    HAS_BROTLI = False


class JSONDatasetMaker():
    """Create and export a dataset containing shared blocks."""

    def __init__(self, logger: Optional[Logger] = None):
        self.__args: dict = None
        self.__prompt = PromptArgumentParser(allow_abbrev=False,
                                      description="Reads VT data and saves chosen phases from it.",
                                      prompt_default=True)
        self.__logger = logger if logger is not None else get_logger()

    def __parse_args(self):
        """Parse arguments."""
        parser = self.__prompt
        parser.add_argument("--output-file-name", help="The absolute path to the output JSON file",
                            default=os.path.join(PROJECT_PATH, "output", "build", "data.json"))
        parser.add_argument("--compressed", help="To compress output data using brotli", default=False, type=bool)
        self.__args = parser.parse_args()

    def run(self):
        """Run the JSONDatasetMaker"""
        # Parse command line arguments
        self.__parse_args()

        if self.__args.compressed and not HAS_BROTLI:
            self.__logger.warning('brotli module not found. Compression not available')
            self.__args.compressed = False

        output_dir = os.path.dirname(self.__args.output_file_name)
        if not os.path.exists(output_dir): # create folders if not exists
            os.makedirs(output_dir)

        # Logic: ask user for
        # 1. create tasks + shared blocks (+ shared block size) (shared_id, shared_bytes in user_defined data)
        # 2. create communications between tasks
        # 3. build config dictionary
        # 4. JSON file output
        config: dict = {}
        action: str = 'Add Task'
        r_id = 1

        tasks: List[Object] = []
        # communications: List[?] = []
        while action != 'Build JSON file':
            action = self.__prompt.prompt(
                'What kind of action ?',
                choices=['Add Task', 'Add Communication', 'Build JSON file'],
                default=action,
                required=True
            )

            if action == 'Add Task':
                # Task information
                i = len(tasks) + 1
                r_id = self.__prompt.prompt(
                    f'Task #{i} : rank id. (Optional)',
                    default=r_id
                )
                user_defined: dict = {}

                # ask for possible shared block appartenance (TODO)

                task = Object(i, r_id, user_defined=user_defined)
                tasks.append(task)
                continue
            elif action == 'Add Communication':
                # prompt from task (id) and to task (id) (TODO)
                continue
            else:
                break

        # build config dictionary (TODO)

        # Convert dict to json
        json_str = json.dumps(config, separators=(',', ':'))
        if self.__args.compressed:
            compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
            with open(self.__args.output_file_name, "wb") as compr_json_file:
                compr_json_file.write(compressed_str)
        else:
            with open(self.__args.output_file_name, "wt", encoding="utf-8") as json_file:
                json_file.write(json_str)

        self.__logger.info(f'Data file generated at {self.__args.output_file_name}')

if __name__ == "__main__":
    JSONDatasetMaker().run()
