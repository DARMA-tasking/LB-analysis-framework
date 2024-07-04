"""
Utility to generate a data set supporting shared blocks by using a specification file.

To call this script either call script with
- `lbaf-vt-data-files-maker` if lbaf package is installed or
- `python src/lbaf/Utils/lbsJSONDataFilesMaker.py`

Script usage examples:

- Generate dataset from specification file
`lbaf-vt-data-files-maker --spec-file=/home/john/data-maker/dataset1-spec.yaml --data-stem=/home/john/data-maker/dataset1`

- Generate dataset from specification file and sample configuration file configured tonuse the generated data stem
`lbaf-vt-data-files-maker --spec-file=/home/john/data-maker/dataset1-spec.yaml --data-stem=/home/john/data-maker/dataset1 --config-file=/home/thomas/data-maker/dataset1-config.yaml`

- Generate dataset from specification defined interactively in CLI
`lbaf-vt-data-files-maker --interactive`

Sample specification: a sample specification can be loaded in the interactive mode and be printed as an example in
either YAML or JSON format.
Other examples can be found as unit tests configuration files in the the tests/unit/config/phases directory

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


# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec("lbaf") is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))

from lbaf import PROJECT_PATH
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.Model.lbsPhase import Phase
from lbaf.Execution.lbsPhaseSpecification import (
    PhaseSpecification, CommunicationSpecification, SharedBlockSpecification, RankSpecification,
    PhaseSpecificationNormalizer
)
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger, Logger
# pylint:disable=C0413:wrong-import-position


class YamlSpecificationDumper(yaml.Dumper):
    """Custom dumper to add indent before list items hyphens."""

    def increase_indent(self, flow=False, indentless=False):
        return super(YamlSpecificationDumper, self).increase_indent(flow, False)


class JSONDataFilesMaker():
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
                "Utility to generate a data set supporting shared blocks by using a specification file.\n" +
                "Note: a sample specification can be loaded in the interactive mode and be printed\n" +
                "as an example in either YAML or JSON format."),
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
        parser.add_argument("--spec-file", help="The path to the specification file. Required.", default=None)
        parser.add_argument("--data-stem", help="Required. The data stem.", required=False)
        parser.add_argument("--compressed", help="To compress output data using brotli", default=False, type=bool)
        parser.add_argument("--config-file", help="The path to the LBAF config file to run using the generated dataset",
                            default=None)
        parser.add_argument("--multiple-sharing", help="Allow specification to define tasks that share more than one"
                                                       "block",
                            default=False, nargs='?', type=bool)
        parser.add_argument("--interactive",
                                help="Add this argument to enter the interactive mode."
                                      "Required arguments might then also be defined in CLI",
                                default=False, nargs='?',
                            type=bool)

        self.__args = parser.parse_args()

    def process_args(self) -> PhaseSpecification:
        """Process input arguments and initialize a working PhaseSpecification instance"""

        # In non interactive mode data-stem and spec-file arguments are required
        if self.__args.interactive is False:
            if self.__args.data_stem is None:
                self.__prompt.print_error("The `data-stem` argument is required")
                self.__logger.info("You can also enter the interactive mode by adding the --interactive argument")
                raise SystemExit(1)

            if self.__args.spec_file is None:
                self.__prompt.print_error("The `spec-file` argument is required")
                self.__logger.info("You can also enter the interactive mode by adding the --interactive argument")
                raise SystemExit(1)

        spec = None
        if self.__args.spec_file:
            spec = self.create_spec_from_file(self.__args.spec_file)

        if spec is None:
            spec: PhaseSpecification = PhaseSpecification({
                "tasks": [],
                "shared_blocks": [],
                "communications": [],
                "ranks": {}
            })

        # Build immediately in non interactive mode
        if self.__args.interactive is False:
            self.build(spec)

        return spec

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
        writer.write({phase.get_id(): phase})
        self.__prompt.print_success("Dataset has been generated.")

    def create_spec_sample(self, use_explicit_keys: bool = False) -> PhaseSpecification:
        """Create a new sample specification as represented by diagram specified in issue #506
        This method implementation indicates also how to cfreate a specification from Python code
        """

        specs = PhaseSpecification({
            "tasks": [2.0, 3.5, 5.0],
            "communications": [
                CommunicationSpecification({
                    "size": 10000.0,  # c1 (size)
                    "from": 0,  # from t1
                    "to": 2  # to t3
                }),
                CommunicationSpecification({
                    "size": 15000.0,  # c2 (size)
                    "from": 1,  # from t2
                    "to": 2  # to t3
                }),
                CommunicationSpecification({
                    "size": 20000.0,  # c3 (size)
                    "from": 2,  # from t3
                    "to": 1  # to t2
                }),
                CommunicationSpecification({
                    "size": 25000.0,  # c4 (size)
                    "from": 0,  # from t1
                    "to": 1  # to t2
                })
            ],
            "shared_blocks": [
                # S1
                SharedBlockSpecification({
                    "size": 10000.0,
                    "home_rank": 0,
                    "tasks": {0, 1}
                }),
                # S2
                SharedBlockSpecification({
                    "size": 15000.0,
                    "home_rank": 1,
                    "tasks": {2}
                })
            ],
            "ranks": {
                0: RankSpecification({"tasks": {0, 1}}),
                1: RankSpecification({"tasks": {2}})
            }
        })

        if use_explicit_keys:
            specs["tasks"] = {comm_id: comm for comm_id, comm in enumerate(specs["tasks"])}
            specs["communications"] = {task_id: task for task_id, task in enumerate(specs["communications"])}
            specs["shared_blocks"] = {block_id: block for block_id, block in enumerate(specs["shared_blocks"])}

        return specs

    def create_spec_from_file(self, file_path) -> Optional[PhaseSpecification]:
        """Create a new specification by loading from a file and returns None if data contain errors"""
        spec = PhaseSpecification()
        with open(file_path, "r", encoding="utf-8") as file_stream:
            if file_path.endswith(".json"):
                spec_dict = json.load(file_stream)
                # in json keys are strings (int not supported by the JSON format) so apply casts as needed
                if "ranks" in spec_dict:
                    spec_dict["ranks"] = {int(rank_id): data for rank_id, data in spec_dict["ranks"].items()}
            else:
                spec_dict = yaml.safe_load(file_stream)

        spec = PhaseSpecificationNormalizer().denormalize(spec_dict)
        try:
            Phase(self.__logger, 0).populate_from_specification(spec, self.__args.multiple_sharing is not False)
            self.__logger.info("Specification is valid !")
        except RuntimeError as e:
            self.__logger.error(f"Specification error: {e}")
            spec = None
            if self.__args.interactive is False:
                raise SystemExit() from e

        return spec

    def print(self, spec: PhaseSpecification, output_format: str = "json"):
        """print a specification to the console"""

        if output_format == "json":
            print("----------- BEGIN JSON -----------")
            print(json.dumps(spec, sort_keys=True, indent=2, separators=(',', ": ")))
            print("----------- END JSON -------------")
        else:
            print("----------- BEGIN YAML -----------")
            print(yaml.dump(spec, indent=2, Dumper=YamlSpecificationDumper, default_flow_style=None))
            print("----------- END YAML -------------")

    def ask_object(self, objects: Union[dict, list], object_type_name: str, can_add: bool = False,
                          can_go_back=False, question: str = None, validate: Optional[Callable] = None, default=None, ):
        """Request user to select a choice in a list of dict keys or list indices"""
        choices = []
        if isinstance(objects, dict):
            choices = [i for i in objects.keys()]
        else:
            choices = [i for i in range(0, len(objects))]
        if can_add:
            choices.append(f"*New {object_type_name}")
        if can_go_back:
            choices.append("*Back")

        choice = self.__prompt.prompt(
            f"Choose {object_type_name}" if question is None else question,
            choices=choices,
            value_type=str,
            required=True,
            default=f"*New {object_type_name}" if can_add and default is None else default, validate=validate)

        if choice == "*Back":
            return "*Back"
        if choice != f"*New {object_type_name}":
            return int(choice)
        else:
            return "*New"

    def make_object(self, parent: Union[list, dict], object_type_name: str, default, update: Callable):
        """Create or update an object in a a list (id is the index) or in a dict (id is the key) for interactive input
        of tasks, communications and shared blocks"""

        object_id = self.ask_object(parent, object_type_name, True, can_go_back=True)

        if object_id == "*Back":
            return


        # retrieve current value
        object_data = (default if object_id == "*New" else (
            parent[object_id] if isinstance(parent, dict) else parent[object_id]))
        object_data = update(object_data, None if object_id == "*New" else object_id)

        if object_id == "*New":
            if isinstance(parent, dict):
                object_id = max(parent.keys(), default=-1) + 1
                object_id = self.__prompt.prompt(
                    f"{object_type_name.capitalize()} id ?", required=True, value_type=int, default=object_id,
                    validate=lambda t_id: f"{object_type_name.capitalize()} id already used"
                    if t_id in parent.keys()
                    else None)
            else:
                object_id = None

        # append or update object in or to the parent list or dict
        if isinstance(parent, dict):
            parent[object_id] = object_data
        else:
            if object_id is not None:
                parent[object_id] = object_data  # update
            else:
                parent.append(object_data)  # create

    def make_task(self, spec: PhaseSpecification):
        """Creates or updates a task in interactive mode"""

        self.make_object(
            spec.get("tasks"),
            "task",
            default=0.0,
            update=lambda time, t_id: (self.__prompt.prompt("Task time ?", required=True, value_type=float, default=time)),
        )

    def update_communication(self, comm, tasks: Union[dict, list]):
        """Ask for communicaton size, from and to in interactive mode"""

        comm["size"] = self.__prompt.prompt(
            "Communication size ?", required=True, value_type=float, default=comm.get("size", 0.0)),
        comm["from"] = self.ask_object(
            tasks,
            object_type_name="task",
            question="From (task id) ?",
            default=comm.get("from", None)
        )
        comm["to"] = self.ask_object(
            tasks,
            object_type_name="task",
            question="To (task id) ?",
            validate=lambda x: "Receiving task must be different from sending task" if int(x) == comm["from"] else None,
            default=comm.get("to", None)
        )
        return comm

    def make_communication(self, spec: PhaseSpecification):
        """Creates or updates a communication in interactive mode"""

        self.make_object(
            spec.get("communications"),
            "communication",
            default=CommunicationSpecification({"size": 0.0}),
            update=lambda comm, comm_id: self.update_communication(comm, spec["tasks"])
        )

    def update_shared_block(self, block, tasks: Union[dict, list], ranks: dict):
        """Ask for shared block size, and tasks in interactive mode"""

        block["size"], = self.__prompt.prompt(
            "Shared block size ?", required=True, value_type=float, default=block.get("size", 0.0)),

        tasks_valid = False
        while not tasks_valid:
            tasks_valid = True
            tasks_csv_default = str.join(",", block["tasks"]) if len(block["tasks"]) > 0 else None
            task_ids = self.__prompt.prompt("Shared block tasks ids (comma separatated) ?",
                                                required=False, value_type=str,default=tasks_csv_default)
            if task_ids is None or task_ids == '':
                block["tasks"] = []
                return block

            try:
                task_ids = [int(t_id) for t_id in task_ids.split(',')]
            except ValueError as ex:
                self.__prompt.print_error(f"Input error: {ex.args[0]}")
                tasks_valid = False
                continue

            n_tasks = len(task_ids)
            task_ids = list(dict.fromkeys(task_ids)) # unique values
            if len(task_ids) < n_tasks:
                self.__logger.warning("Duplicated task(s) found and removed")

            all_tasks = tasks.keys() if isinstance(tasks, dict) else list(range(len(tasks)))
            for t in task_ids:
                if not t in all_tasks:
                    tasks_valid = False
                    self.__prompt.print_error(f"Task {t} not found")
                    break

        block["tasks"] = task_ids

        # Try to find some default home as the first task ranks
        default_home = block.get("home_rank", None)
        if task_ids and default_home is None:
            for rank_id, rank_spec in ranks.items():
                # If any ranks task id in ranks tasks set default home to that rank
                for ranks_task_id in rank_spec["tasks"]:
                    if ranks_task_id in task_ids:
                        default_home = rank_id
                        break

                if default_home:
                    break

        block["home_rank"] = self.__prompt.prompt(
            "Home rank ?", required=True, value_type=int, default=block.get("home_rank", default_home))

        return block

    def make_shared_block(self, spec: PhaseSpecification):
        """Creates or updates a communication in interactive mode"""

        self.make_object(
            spec.get("shared_blocks"),
            "shared block",
            default=SharedBlockSpecification({"size": 0.0, "tasks": [], "home_rank": None}),
            update=lambda block, block_id: self.update_shared_block(block, spec["tasks"], spec["ranks"])
        )

    def update_rank(self, rank: RankSpecification, spec: PhaseSpecification):
        """Ask for rank id (if new) and tasks in interactive mode"""

        all_tasks = spec["tasks"].keys() if isinstance(spec["tasks"], dict) else list(range(len(spec["tasks"])))
        valid = False
        while not valid:
            valid = True
            tasks_csv_default = str.join(",", rank["tasks"]) if len(rank["tasks"]) > 0 else None
            task_ids_csv = self.__prompt.prompt("Rank tasks (comma separated) ?",
                                            required=False, value_type=str, default=tasks_csv_default)
            try:
                task_ids = [int(t_id) for t_id in task_ids_csv.split(',')] if task_ids_csv is not None else []
            except ValueError as ex:
                self.__prompt.print_error(f"Input error: {ex.args[0]}")
                valid = False
                continue

            n_tasks = len(task_ids)
            task_ids = list(dict.fromkeys(task_ids)) # unique values
            if len(task_ids) < n_tasks:
                self.__logger.warning("Duplicated task(s) found and removed")

            for t in task_ids:
                if not t in all_tasks:
                    self.__prompt.print_error(f"Task {t} not found")
                    valid = False
                    break
                for r_id, r in spec["ranks"].items():
                    if r != r_id and t in r["tasks"]:
                        self.__prompt.print_error(f"Task {t} already defined on rank {r_id}")
                        valid = False
                        break
                if not valid:
                    break

            rank["tasks"] = task_ids
        return rank

    def make_rank(self, spec: PhaseSpecification):
        """Creates or updates a rank in interactive mode"""

        self.make_object(
            spec.get("ranks"),
            "rank",
            default=RankSpecification({"tasks": []}),
            update=lambda rank, rank_id: self.update_rank(rank, spec)
        )

    def run_extra_action(self, action: str, spec: PhaseSpecification):
        """Run an extra action"""

        if action == "Extra: load sample":
            spec = self.create_spec_sample(use_explicit_keys=True)
            action = "Build"
        elif action == "Extra: print":
            frmt = self.__prompt.prompt("Format ?", choices=["yaml", "json"], required=True, default="yaml")
            self.print(PhaseSpecificationNormalizer().normalize(spec), frmt)
        elif action == "Extra: save":
            frmt = None
            while frmt is None:
                path = self.__prompt.prompt("Path ?", required=True)
                output_dir = f"{os.sep}".join(path.split(os.sep)[:-1])
                frmt = "json" if path.endswith(".json") \
                        else "yaml" if path.endswith(".yaml") or path.endswith(".yml") \
                        else None
                if frmt is None:
                    self.__prompt.print_error("Specification file path must end with either .json, .yml, .yaml")

            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)

            with open(path, "wt", encoding="utf-8") as o_file:
                o_file.write(PhaseSpecificationNormalizer().normalize(spec), frmt)

    def run_action(self, action: str, spec: PhaseSpecification):
        """Run an action"""

        if action == "Make Task":
            self.make_task(spec)
        elif action == "Make Shared block":
            self.make_shared_block(spec)
        elif action == "Make Communication":
            if (isinstance(spec["tasks"], dict) and len(spec["tasks"]) < 2) or (
                isinstance(spec["tasks"], list) and len(spec["tasks"]) < 2):
                self.__prompt.print_error("To create a communication please create at least 2 tasks")
                action = "Make Task"
            else:
                self.make_communication(spec)
        elif action == "Make Rank":
            self.make_rank(spec)
        elif action == "Build":
            self.__args.data_stem = self.__prompt.prompt(
                "Data stem ?",
                default=(os.path.join(PROJECT_PATH, "output", "maker", "data",
                                        self.__datetime.strftime("%y%m%d%H%M%S"), "data")
                            ) if self.__args.data_stem is None else self.__args.data_stem
            )
            try:
                self.build(spec)
                action = "Extra: run"
            except RuntimeError as e:
                self.__prompt.print_error(e.args[0])
        elif action == "Extra: load file":
            file_path = self.__prompt.prompt("File path (Yaml or Json) ?", required=True)
            if s:= self.create_spec_from_file(file_path) is not None:
                spec = s
        elif action == "Extra: Run":
            if self.__args.config_file is None:
                self.__args.config_file  = self.__prompt.prompt(
                "LBAF Configuration file ?", required=True
            )

            if not os.path.exists(self.__args.config_file):
                self.__prompt.print_error(f"Run configuration does not exist at {self.__args.config_file}."
                                            "Please create the run configuration.")
            else:
                subprocess.run(["python", f"{PROJECT_PATH}/src/lbaf", "-c", self.__args.config_file], check=True)
        else:
            self.run_extra_action(action, spec)

    def run(self):
        """Run the JSONDatasetMaker"""

        # Parse command line arguments
        self.__parse_args()

        spec: PhaseSpecification = self.process_args()
        if self.__args.interactive is False:
            return

        # Loop on interactive mode available actions
        action: str = "Make Task"  # default action is a sample
        while action != "Build JSON file":
            action = self.__prompt.prompt(
                "What kind of action ?",
                choices=[
                    "Make Task",
                    "Make Shared block",
                    "Make Communication",
                    "Make Rank",
                    "Build",
                    "Extra: load file",
                    "Extra: run",
                    "Extra: load sample",
                    "Extra: print",
                    "Extra: save",
                    "Exit"
                ],
                default=action,
                required=True
            )

            if action == "Exit":
                break
            else:
                try:
                    self.run_action(action, spec)
                # Catch any exception so that only the user can choose to exit the script (interactive) loop
                except Exception as err: # pylint:disable=W0718:broad-exception-caught
                    self.__prompt.print_error(err.args[0])

if __name__ == "__main__":
    JSONDataFilesMaker().run()
