"""
Utility to create and export a data set supporting shared blocks by using a specification file.

To call this script either call script with
- `lbaf-json-dataset-maker` or
- `python src/lbaf/Utils/lbsJSONDatasetMaker.py`

Run examples:
`lbaf-json-dataset-maker --spec-file=/home/john/data-maker/dataset1.json` --data-stem=/home/john/data-maker/dataset1
`lbaf-json-dataset-maker --interactive`

Note: `lbaf-json-dataset-maker` is the console script name.
      It is also possible to run by calling `python src/lbaf/Utils/lbsJSONDatasetMaker.py`

A sample specification can be generated in the interactive mode and be printed as an example in
either Yaml or JSON format.

"""
from argparse import RawTextHelpFormatter
from datetime import datetime
import importlib
import importlib.util
import os
import sys
from typing import Optional, Union, Callable
import subprocess
import json
import yaml
from lbaf.Model.lbsPhase import Phase
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.Execution.lbsPhaseSpecification import (
    PhaseSpecification, CommunicationSpecification, SharedBlockSpecification, RankSpecification,
    PhaseSpecificationNormalizer
)

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec("lbaf") is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger, Logger
# pylint:disable=C0413:wrong-import-position


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

        self.__prompt = PromptArgumentParser(
            allow_abbrev=False,
            description=(
                "Utility to create and export a data set supporting shared blocks by using a specification file.\n" +
                "Note: a sample specification can be generated in the interactive mode and be printed\n" +
                "as an example in either Yaml or JSON format."),
            prompt_default=False,
            formatter_class=RawTextHelpFormatter
        )

        """The argument parser and prompter"""

        self.__logger = logger if logger is not None else get_logger()
        """The logger"""

        self.__datetime = datetime.now()
        """The init datetime"""

    def __parse_args(self):
        """Parse arguments."""

        parser = self.__prompt
        parser.add_argument("--interactive", help="Set True to enter the interactive mode", default=False, nargs='?',
                                             type=bool)
        parser.add_argument("--spec-file", help="The path to the specification file", default=None)
        parser.add_argument("--data-stem", help="The data stem", required=False)
        parser.add_argument("--compressed", help="To compress output data using brotli", default=False, type=bool)
        parser.add_argument("--output-config-file", help="The path to generate a default LBAF config file",
                            default=None)

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
        self.__prompt.print_success("Dataset has been generated.")

    def get_run_configuration_sample(self):
        """Return a local configuration fiel for the LBAF application for the generated dataset"""
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

    def create_spec_from_sample(self, use_explicit_keys: bool=False) -> PhaseSpecification:
        """Create a new sample specification as represented by diagram specified in issue #506"""

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

        if use_explicit_keys:
            specs["tasks"] = {comm_id: comm for comm_id, comm in enumerate(specs["tasks"])}
            specs["communications"] = {task_id: task for task_id, task in enumerate(specs["communications"])}
            specs["shared_blocks"] = {block_id: block for block_id, block in enumerate(specs["shared_blocks"])}

        return specs

    def create_spec_from_file(self, file_path) -> PhaseSpecification:
        """Create a new specification by loading from a file"""
        spec = PhaseSpecification()
        with open(file_path, "r", encoding="utf-8") as file_stream:
            if file_path.endswith(".json"):
                spec_dict = json.load(file_stream)
                # in json keys are strings (int not supported by the JSON format) so apply casts as needed
                if "ranks" in spec_dict:
                    spec_dict["ranks"] = { int(rank_id):data for rank_id,data in spec_dict["ranks"].items() }
            else:
                spec_dict = yaml.safe_load(file_stream)

        spec = PhaseSpecificationNormalizer().denormalize(spec_dict)
        return spec

    def create_run_configuration_sample(self, output_path: str):
        """Write some sample configuration to the specified path to run LBAF using the generated data set"""

        local_conf = self.get_run_configuration_sample()

        output_dir = f"{os.sep}".join(output_path.split(os.sep)[:-1])
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        with open(output_path, "wt", encoding="utf-8") as file:
            yaml.dump(local_conf, file)

        self.__logger.info(f"Configuration generated at ${output_path}")

    def print(self, spec: PhaseSpecification, output_format: str="json"):
        """print a specification to the console"""

        if output_format == "json":
            print ("----------- BEGIN JSON -----------")
            print(json.dumps(spec, sort_keys=True, indent=2, separators=(',', ': ')))
            print ("----------- END JSON -------------")
        else:
            print ("----------- BEGIN YAML -----------")
            print(yaml.dump(spec, indent=2, Dumper=YamlSpecificationDumper, default_flow_style=None))
            print ("----------- END YAML -------------")


    def run_non_interactive(self):
        """Builds data directly by using the input arguments values"""

        if self.__args.data_stem is None:
            self.__prompt.print_error("The `data-stem` argument is required")
            self.__logger.info("You can also enter the interactive mode by adding the --interactive argument")
            raise SystemExit(1)

        if self.__args.spec_file is None:
            self.__prompt.print_error("The `spec-file` argument is required")
            self.__logger.info("You can also enter the interactive mode by adding the --interactive argument")
            raise SystemExit(1)

        spec = self.create_spec_from_file(self.__args.spec_file)
        self.build(spec)
        # Optionally create a config file to run LBAF with the generated data
        if self.__args.output_config_file is not None:
            self.create_run_configuration_sample(self.__args.output_config_file)

    def create_or_update_object(self, parent: Union[list,dict], object_type_name: str, default, update: Callable):
        """Create an object in parent list or dict for interactive input of tasks, communications and shared blocks"""

        if isinstance(parent, dict):
            choices = [str(i) for i in parent.keys()]
        else:
            choices = [str(i) for i in range(0, len(parent))]
        choices.append(f"*New {object_type_name}")

        object_choice = self.__prompt.prompt("Choose task", choices=choices, value_type=str, required=True,
                                                        default=f"*New {object_type_name}")
        # retrieve current value
        object_value = (default if object_choice == "*New task" else (
                            parent[int(object_choice)]
                            if isinstance(parent, dict)
                            else parent[int(object_choice)]
                        )
                    )
        object_value = update(object_value)

        object_id = None
        if object_choice == f"*New {object_type_name}":
            if isinstance(parent, dict):
                object_id = max(parent.keys(), default=-1) + 1
                object_id = self.__prompt.prompt(
                    f"{object_type_name.capitalize()} id ?", required=True, value_type=int, default=object_id,
                                validate= lambda t_id: f"{object_type_name.capitalize()} id already used"
                                          if t_id in parent.keys()
                                          else None)
        else:
            object_id = int(object_choice)

        # append or update object in or to the parent list or dict
        if isinstance(parent, dict):
            parent[object_id] = object_value
        else:
            if object_id:
                parent[object_id] = object_value # update
            else:
                parent.append(object_value) # create


    def create_or_update_task(self, spec: PhaseSpecification):
        """Creates or updates a task interactive mode"""

        self.create_or_update_object(
            spec.get("tasks"),
            "task",
            default=0.0,
            update=lambda time: (self.__prompt.prompt("Task time ?", required=True, value_type=float, default=time)),
        )

    def create_or_update_communication(self, spec: PhaseSpecification):
        """Creates or updates a communication in interactive mode"""

        # TODO: WIP here
        self.create_or_update_object(
            spec.get("communications"),
            "communication",
            default=0.0,
            update=lambda comm: ( # TODO: find how how to run callback if not lambda in python
                comm["size"] = self.__prompt.prompt("Communication size ?", required=True, value_type=float),
                comm["from"] = self.__prompt.prompt("From (task id or index) ?", required=True, value_type=int,
                    validate= lambda v: (
                        raise NotImplementedError("TODO: check unique not equal to from + task id exist")
                    )
                )
                comm["to"] = self.__prompt.prompt("To (task id or index) ?", required=True, value_type=int,
                    validate= lambda v: (
                        raise NotImplementedError("TODO: check unique not equal to from + task id exist")
                    )
                )
            )            
        )

    def run(self):
        """Run the JSONDatasetMaker"""

        # Parse command line arguments
        self.__parse_args()

        # if --no-prompt explicit and all required elements run immediately
        if self.__args.interactive is False:
            self.run_non_interactive()
            return

        # Logic: ask user for
        # 1. create tasks + shared blocks (+ shared block size) (shared_id, shared_bytes in user_defined data)
        # 2. create communications between tasks
        # 3. build config dictionary
        # 4. JSON file output

        # Specification of the phase to make
        spec: PhaseSpecification = PhaseSpecification({
            "tasks": [],
            "shared_blocks": [],
            "communications": [],
            "ranks": {}
        })

        action: str = "Load sample specification" # default action is a sample
        while action != "Build JSON file":
            action = self.__prompt.prompt(
                "What kind of action ?",
                choices=[
                    "Specification: load file",
                    "Specification: load sample",
                    "Task: create or update",
                    "Communication: add",
                    "Add shared block",
                    "Define rank",
                    "Create Run Configuration",
                    "Build",
                    "Run",
                    "Print (JSON)",
                    "Print (YAML)",
                    "Exit"
                ],
                default=action,
                required=True
            )
            if action == "Specification: load file":
                file_path = self.__prompt.prompt("File path (Yaml or Json) ?", required=True)
                spec = self.create_spec_from_file(file_path)
            elif action == "Specification: load sample":
                spec = self.create_spec_from_sample(use_explicit_keys=True)
                action = "Build"
            elif action == "Task: create or update":
                self.create_or_update_task(spec)
            elif action == "Communication: create or update":
                self.create_or_update_communication(spec)
            elif action == "Add shared block":
                block_id = None
                if isinstance(spec.get("tasks", []), dict):
                    block_id = self.__prompt.prompt("Shared block id ?", required=True, value_type=int)
                task_ids = self.__prompt.prompt("Shared block tasks (ids or indices) ?", required=True, value_type=str)
                task_ids = [int(t_id) for t_id in task_ids.split(',')]
                block = SharedBlockSpecification({
                    "size": self.__prompt.prompt("Shared block size ?", required=True, value_type=float),
                    "tasks": task_ids,
                })
                if block_id is not None:
                    spec["shared_blocks"][block_id] = block
                else:
                    spec["shared_blocks"].append(block)
            elif action == "Define rank":
                rank_id = self.__prompt.prompt("Rank id ?", required=True, value_type=int)
                task_ids = self.__prompt.prompt("Rank tasks (comma separated) ?", required=True, value_type=str)
                task_ids = [int(t_id) for t_id in task_ids.split(',')]
                com_ids = self.__prompt.prompt("Rank communications (comma separated) ?", required=True, value_type=str)
                com_ids = [int(t_id) for t_id in task_ids.split(',')]
                spec["ranks"][rank_id] = RankSpecification({
                    "tasks": task_ids,
                    "communications": com_ids
                })
            elif action == "Print (JSON)":
                self.print(PhaseSpecificationNormalizer().normalize(spec), "json")
            elif action == "Print (YAML)":
                self.print(PhaseSpecificationNormalizer().normalize(spec), "yaml")
            elif action == "Build":
                self.__args.data_stem = self.__prompt.prompt(
                    "Data stem ?",
                    default=(os.path.join(PROJECT_PATH, "output", "maker", "data",
                                            self.__datetime.strftime("%y%m%d%H%M%S"), "data")
                    ) if self.__args.data_stem is None else self.__args.data_stem
                )
                try:
                    self.build(spec)
                    action="Create Run Configuration"
                except RuntimeError as e:
                    self.__prompt.print_error(e.args[0])
            elif action == "Create Run Configuration":
                if self.__args.data_stem is None:
                    self.__prompt.print_error("Please build or set data-stem argument")
                    continue

                dataset_name = self.__args.data_stem.split(os.sep)[-1]
                self.__args.output_config_file = self.__prompt.prompt(
                    "Output configration file path ?",
                    default=(os.path.join(PROJECT_PATH, "output", "maker", "config",
                                          self.__datetime.strftime("%y%m%d%H%M%S"), f"{dataset_name}.yaml")
                    ) if self.__args.output_config_file is None else self.__args.output_config_file,
                    required=True
                )

                self.create_run_configuration_sample(self.__args.output_config_file)
                action="Run"
            elif action == "Run":
                if self.__args.output_config_file is None:
                    self.__prompt.print_error("Run configuration is not defined. Please create a run configuration !")
                    continue
                elif not os.path.exists(self.__args.output_config_file):
                    self.__prompt.print_error(f"Run configuration does not exist at {self.__args.output_config_file}." \
                                        "Please create the run configuration.")

                subprocess.run(["python", "src/lbaf", "-c", self.__args.output_config_file], check=True)
            elif action == "Exit":
                break

if __name__ == "__main__":
    JSONDatasetMaker().run()
