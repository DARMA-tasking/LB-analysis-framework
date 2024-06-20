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
from typing import Optional
import yaml
from lbaf.Model.lbsPhase import Phase
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.Execution.lbsPhaseSpecification import PhaseSpecification

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
        self.__datetime = datetime.now()

    def __parse_args(self):
        """Parse arguments."""
        parser = self.__prompt
        parser.add_argument("--data-stem", help="The data stem",
                            default=os.path.join(PROJECT_PATH, "data", "generated",
                            self.__datetime.strftime("%y%m%d%H%M%S"), "data"))
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
        specs: PhaseSpecification = { "tasks": [], "shared_blocks": [], "communications": [], "ranks": {} }

        action: str = "New Sample"
        while action != "Build JSON file":
            action = self.__prompt.prompt(
                "What kind of action ?",
                choices=[
                    "New Task",
                    "New Communication",
                    "New Sample",
                    "Build",
                    "Create Run Configuration",
                    "Dump",
                    "Exit"
                ],
                default=action,
                required=True
            )

            if action == "New Task":
                task_id = len(specs["tasks"])
                t_time = self.__prompt.prompt(
                    f"Task #{task_id} : time.",
                    value_type=float,
                    required=True)
                specs["tasks"].append(t_time)
                continue
            elif action == "New Communication":
                # prompt from communication size (TODO)
                continue
            elif action == "New Rank":
                # prompt from rank tasks (space separated)
                continue
            elif action == "New Sample":
                specs = PhaseSpecification.create_sample()
                action = "Build"
            elif action == "Dump":
                print(specs)
            elif action == "Build":
                try:
                    # create and populate phase
                    phase = Phase(self.__logger, 0)
                    phase.populate_from_specification(specs)
                    # Save
                    writer_parameters: dict = {
                        "compressed": self.__args.compressed,
                        "json_output_suffix": "json",
                    }

                    output_dir = f"{os.sep}".join(self.__args.data_stem.split(os.sep)[:-1])
                    if not os.path.isdir(output_dir):
                        os.makedirs(output_dir)

                    writer = VTDataWriter(self.__logger, None, self.__args.data_stem, writer_parameters)
                    writer.write({ phase.get_id(): phase })
                    self.__logger.info("Dataset has been generated.\n")
                    action="Create Run Configuration"
                    continue
                except RuntimeError as e:
                    self.__logger.error(e.args[0])
                    continue
            elif action == "Create Run Configuration":
                name =  self.__args.data_stem.split(os.sep)[-1]
                local_conf = {
                    "from_data": {
                        "data_stem": self.__args.data_stem,
                        "phase_ids": [0]
                    },
                    "check_schema": True,
                    "work_model": {
                        "name": "AffineCombination",
                        "parameters": {
                            "alpha": 0.0,
                            "beta": 1.0,
                            "gamma": 0.0
                        }
                    },
                    "algorithm": {
                        "name": "InformAndTransfer",
                        "phase_id": 0,
                        "parameters": {
                            "n_iterations": 8,
                            "n_rounds": 2,
                            "fanout": 2,
                            "order_strategy": "arbitrary",
                            "transfer_strategy": "Recursive",
                            "criterion": "Tempered",
                            "max_objects_per_transfer": 8,
                            "deterministic_transfer": True
                        }
                    },
                    "output_dir": f"{PROJECT_PATH}/output",
                    "output_file_stem": "output_file"
                }

                output_dir = os.path.join(PROJECT_PATH, "config", "generated", self.__datetime.strftime("%y%m%d%H%M%S"))
                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)

                with open(os.path.join(output_dir, f"{name}.yaml"), "wt", encoding="utf-8") as file:
                    yaml.dump(local_conf, file)

                self.__logger.info(f"Configuration generated at config/{name}")
                self.__logger.info(f"To run just exit and run `lbaf --configuration=config/{name}`")
                action="Exit"
            elif action == "Exit":
                break

if __name__ == "__main__":
    JSONDatasetMaker().run()
