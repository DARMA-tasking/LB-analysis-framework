"""
Utility to create and export a data file supporting shared blocks
To call this script either call package console script `lbaf-json-dataset-maker`
or call python src/lbaf/Utils/lbsJSONDatasetMaker.py
"""
from datetime import datetime
import importlib
import importlib.util
import os
import sys
from typing import Optional, List, Dict, TypedDict, Union
from lbaf.Model.lbsObject import Object
from lbaf.Model.lbsPhase import Phase
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.Execution.lbsDatasetSpecification import DatasetSpecification

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec("lbaf") is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger, Logger
# pylint:disable=C0413:wrong-import-position

class JSONDatasetMaker():
    """Create and export a dataset containing shared blocks."""

    def __init__(self, logger: Optional[Logger] = None):
        self.__args: dict = None
        self.__prompt = PromptArgumentParser(allow_abbrev=False,
                                      description="Create a VT Dataset and output the dataset using the VTDataWriter.",
                                      prompt_default=True)
        self.__logger = logger if logger is not None else get_logger()

    def __parse_args(self):
        """Parse arguments."""
        parser = self.__prompt
        parser.add_argument("--data-stem", help="The data stem",
                            default=os.path.join(PROJECT_PATH, "output", "data",
                            datetime.now().strftime("%y%m%d%H%M%S"), "data"))
        parser.add_argument("--compressed", help="To compress output data using brotli", default=False, type=bool)
        self.__args = parser.parse_args()

    def run(self):
        """Run the JSONDatasetMaker"""
        # Parse command line arguments
        self.__parse_args()

        # Logic: ask user for
        # 1. create tasks + shared blocks (+ shared block size) (shared_id, shared_bytes in user_defined data)
        # 2. create communications between tasks
        # 3. build config dictionary
        # 4. JSON file output

        # Specification of the phase to make
        specs: DatasetSpecification = { "tasks": [], "shared_blocks": [], "communications": [], "ranks": {} }

        action: str = 'New Task'
        while action != 'Build JSON file':
            action = self.__prompt.prompt(
                'What kind of action ?',
                choices=[
                    'New Task',
                    'New Communication',
                    'Build',
                    'Exit'
                ],
                default=action,
                required=True
            )

            if action == 'New Task':
                task_id = len(specs['tasks'])
                t_time = self.__prompt.prompt(
                    f'Task #{task_id} : time.',
                    value_type=int,
                    required=True)
                specs['tasks'].append(t_time)
                continue
            elif action == 'New Communication':
                # prompt from communication size (TODO)
                continue
            elif action == 'New Rank':
                # prompt from rank tasks (space separated)
                continue
            elif action == 'Build':
                # create and populate phase
                phase = Phase(self.__logger, 0)
                phase.populate_from_specification(specs)
                # Save
                writer_parameters: dict = {
                    "compressed": self.__args.compressed,
                    "json_output_suffix": "json",
                }
                writer = VTDataWriter(self.__logger, None, self.__args.data_stem, writer_parameters)
                writer.write({ phase.get_id(): phase })
                self.__logger.info("Dataset has been generated.\n")
                continue
            elif action == "Exit":
                break

if __name__ == "__main__":
    JSONDatasetMaker().run()
