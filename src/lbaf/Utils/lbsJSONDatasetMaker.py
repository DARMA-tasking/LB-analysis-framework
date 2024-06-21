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
from typing import Optional, cast
import subprocess
import json
import yaml
from lbaf.Model.lbsPhase import Phase
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.Execution.lbsPhaseSpecification import (
    PhaseSpecification, CommunicationSpecification, SharedBlockSpecification, RankSpecification)

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec("lbaf") is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger, Logger
# pylint:disable=C0413:wrong-import-position

def json_set_serializer(obj):
    """Serialize a python set for json"""
    if isinstance(obj, set):
        return dict({ "__python_set": list(obj) })

def json_set_deserializer(dct):
    """Deserialize a python set for json"""
    if '__python_set' in dct:
        return set(dct['__python_set'])
    return dct


class YamlSpecificationDumper(yaml.Dumper):
    """Custom dumper to add indent before list items hyphens."""

    def increase_indent(self, flow=False, indentless=False):
        return super(YamlSpecificationDumper, self).increase_indent(flow, False)


class JSONDatasetMaker():
    """Provides generation tools for VT Data using phase specification input.
    It internally use 
    - the `populate_from_specification` method from the Phase class for building the phase instance
    - the VTDataWriter to write data files
    """

    def __init__(self, logger: Optional[Logger] = None):
        """Initializes an instance of the JSONDatasetMaker utility class"""

        self.__args: dict = None
        """The input arguments"""

        self.__prompt = PromptArgumentParser(allow_abbrev=False,
                                      description="Create a VT Dataset and output the dataset using the VTDataWriter.",
                                      prompt_default=False)
        """The argument parser and prompter"""

        self.__logger = logger if logger is not None else get_logger()
        """The logger"""

        self.__datetime = datetime.now()
        """The init datetime"""

    def __parse_args(self):
        """Parse arguments."""

        parser = self.__prompt
        parser.add_argument("--data-stem", help="The data stem", required=False)
        parser.add_argument("--compressed", help="To compress output data using brotli", default=False, type=bool)
        parser.add_argument("--output-config-file", help="To config file output path", default=None)
        self.__args = parser.parse_args()

    def build(self, specs):
        """Build the data set"""

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

    def get_local_run_conf(self):
        """Returns a local configuration fiel for the LBAF application for the generated dataset"""
        return {
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
                    "fanout": 1,
                    "order_strategy": "arbitrary",
                    "transfer_strategy": "Recursive",
                    "criterion": "Tempered",
                    "max_objects_per_transfer": 8,
                    "deterministic_transfer": True
                }
            },
            "logging_level": "debug",
            "output_dir": f"{PROJECT_PATH}/output",
            "output_file_stem": "output_file"
        }

    def create_sample_spec(self) -> PhaseSpecification:
        """Creates a new sample specification as represented by diagram specified in issue #506"""

        specs = PhaseSpecification({
            'tasks': [2.0, 3.5, 5.0],
            'communications': [
                CommunicationSpecification({
                    "size": 10000.0, # c1 (size)
                    "from": 0, # from t1
                    "to": 2 # to t3
                }),
                CommunicationSpecification({
                    "size": 15000.0, # c2 (size)
                    "from": 1, # from t2
                    "to": 2 # to t3
                }),
                CommunicationSpecification({
                    "size": 20000.0, # c3 (size)
                    "from": 2, # from t3
                    "to": 1 # to t2
                }),
                CommunicationSpecification({
                    "size": 25000.0, # c4 (size)
                    "from": 0, # from t1
                    "to": 1 # to t2
                })
            ],
            "shared_blocks": [
                # S1
                SharedBlockSpecification({
                    'size': 10000.0,
                    'tasks': { 0, 1 }
                }),
                #S2
                SharedBlockSpecification({
                    'size': 15000.0,
                    'tasks': { 2 }
                })
            ],
            "ranks": {
                0: RankSpecification({ "tasks": { 0, 1 }, "communications": {0, 3}}),
                1: RankSpecification({ "tasks": { 2 }, "communications": {1, 2} })
            }
        })

        return specs

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
        spec: PhaseSpecification = { "tasks": [], "shared_blocks": [], "communications": [], "ranks": {} }

        action: str = "Load sample specification" # default action is a sample
        while action != "Build JSON file":
            action = self.__prompt.prompt(
                "What kind of action ?",
                choices=[
                    "Load specification from file",
                    "Load sample specification",
                    "Create Run Configuration",
                    "Build",
                    "Run",
                    "Dump",
                    "Exit"
                ],
                default=action,
                required=True
            )
            if action == "Load specification from file":
                file_path = self.__prompt.prompt("File path (Yaml or Json) ?", required=True)
                spec = PhaseSpecification()
                with open(file_path, "r", encoding="utf-8") as file_stream:
                    if file_path.endswith(".json"):
                        spec_dict = json.load(file_stream, object_hook=json_set_deserializer)
                        # in json keys are strings (int not supported by the JSON format) so apply casts as needed
                        if "ranks" in spec_dict:
                            spec_dict["ranks"] = { int(rank_id):data for rank_id,data in spec_dict["ranks"].items() }
                    else:
                        spec_dict = yaml.safe_load(file_stream)
                spec = cast(PhaseSpecification, spec_dict)
            elif action == "Load sample specification":
                spec = self.create_sample_spec()
                action = "Build"
            elif action == "Dump":
                print ("----------- BEGIN JSON -----------")
                print(json.dumps(spec, sort_keys=True, indent=4, separators=(',', ': '), default=json_set_serializer))
                print ("----------- END JSON -------------")
                print("")
                print ("----------- BEGIN YAML -----------")
                print(yaml.dump(spec, indent=4, Dumper=YamlSpecificationDumper))
                print ("----------- END YAML -------------")
            elif action == "Build":
                # enable user to choose data stem only when building
                if self.__args.data_stem is None:
                    self.__args.data_stem = self.__prompt.prompt("Data stem ?",
                        default=os.path.join(PROJECT_PATH, "output", "maker", "data",
                                             self.__datetime.strftime("%y%m%d%H%M%S"), "data"))
                try:
                    self.build(spec)
                    action="Create Run Configuration"
                except RuntimeError as e:
                    self.__logger.error(e.args[0])
            elif action == "Create Run Configuration":
                if self.__args.data_stem is None:
                    self.__logger.error("Please build or set data-stem argument")
                    continue

                name =  self.__args.data_stem.split(os.sep)[-1]
                # enable user to choose data stem only when building
                if self.__args.output_config_file is None:
                    self.__args.output_config_file = self.__prompt.prompt("Output configration file path ?",
                        default=os.path.join(PROJECT_PATH, "output", "maker", "config",
                                            self.__datetime.strftime("%y%m%d%H%M%S"), f"{name}.yaml"),
                        required=True)

                local_conf = self.get_local_run_conf()

                output_dir = f"{os.sep}".join(self.__args.output_config_file.split(os.sep)[:-1])
                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)

                with open(self.__args.output_config_file, "wt", encoding="utf-8") as file:
                    yaml.dump(local_conf, file)

                self.__logger.info(f"Configuration generated at ${self.__args.output_config_file}")
                action="Run"
            elif action == "Run":
                if self.__args.output_config_file is None:
                    self.__logger.error("Run configuration is not defined. Please create it !")
                    continue
                elif not os.path.exists(self.__args.output_config_file):
                    self.__logger.error(f"Run configuration does not exist at {self.__args.output_config_file}." \
                                        "Please create the run configuration.")

                subprocess.run(["python", "src/lbaf", "-c", self.__args.output_config_file], check=True)
            elif action == "Exit":
                break

if __name__ == "__main__":
    JSONDatasetMaker().run()
