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
from typing import Optional, List, Dict
from ..Model.lbsObject import Object
from ..Model.lbsPhase import Phase
from ..IO.lbsVTDataWriter import VTDataWriter

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
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
                            datetime.now().strftime("%y%m%d%H%M%S"), 'data'))
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

        
        r_id = 1

        tasks: List[Object] = []
        phase_specs: Dict[int,dict] = {} # phase specifications

        # Ask for number of ranks and number of phases first
        n_ranks = self.__prompt.prompt('Number of ranks ?', value_type="int", default=2)
        n_phases = self.__prompt.prompt('Number of phases ?', value_type="int", default=2)

        # should assign rank to phases ranks

        for i in range(n_phases):
            rank_ids = self.__prompt.prompt(
                f"Phase {i}: ranks (Comma separated rank ids, or '*' for all) ?",
                default='*',
                required=True
            )
            phase_specs[i] = {
                "communications": [],
                "objects": [],
                "rank_ids": rank_ids == '*' and range(n_ranks) or rank_ids.explode(',')
            }

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
                # Task information
                i = len(tasks) + 1
                r_id = self.__prompt.prompt(
                    f'Task #{i} : rank id. (Optional)',
                    value_type="int",
                    default=r_id
                )
                user_defined: dict = {}
                # ask for possible shared block appartenance (TODO)

                task = Object(i, r_id, user_defined=user_defined)
                tasks.append(task)
                continue
            elif action == 'New Communication':
                # prompt from task (id) and to task (id) (TODO)
                continue
            elif action == 'Build':
                # populate phases
                phases: Dict[int,Phase] = {}
                for p_id, phase_specs in phase_specs.items():
                    phases[p_id] = Phase(self.__logger, p_id)
                    self.__logger.info(f'Populating phase {p_id}.\n')
                    phases[p_id].populate_from_specification(phase_specs)
                # Save
                writer_parameters: dict = {
                    'compressed': self.__args.compressed,
                    'json_output_suffix': 'json',
                }
                writer = VTDataWriter(self.__logger, None, self.__args.data_stem, writer_parameters)
                writer.write(phases)
                self.__logger.info('Dataset has been generated.\n')
                continue
            elif action == 'Exit':
                break        

if __name__ == "__main__":
    JSONDatasetMaker().run()
