"""
Utility to generate a data set supporting shared blocks by using a specification file.

To call this script either call script with
- `lbaf-vt-data-files-maker` if lbaf package is installed or
- `python src/lbaf/Utils/lbsJSONDataFilesMaker.py`

Script usage examples:

- Generate dataset from specification file
`lbaf-vt-data-files-maker --spec-file=/home/john/data-maker/dataset1-spec.yaml --data-stem=/home/john/data-maker/dataset1`

- Generate dataset from specification file and sample configuration file configured to use the generated data stem
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
from typing import Optional, Union, Callable, Set, Tuple
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
    TaskSpecification, PhaseSpecificationNormalizer
)
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger, Logger
# pylint:disable=C0413:wrong-import-position


class YamlSpecificationDumper(yaml.Dumper):
    """Custom dumper to add indent before list items hyphens."""

    def increase_indent(self, flow=False, indentless=False):
        return super(YamlSpecificationDumper, self).increase_indent(flow, False)


class Util:
    """Utility class with common useful static methods for the maker"""

    @staticmethod
    def cast(value: Union[float, str, int], value_type: Union[float, str, int]):
        """Cast from and to a simple type. If object is already the correct target type it is returned as is"""

        if value_type is not None and not isinstance(value, value_type):
            return value_type(value)

    @staticmethod
    def to_dict(items: Union[dict, list], element_type=None):
        """Get elements as a dict with optional element type conversion"""

        if isinstance(items, dict) and element_type is None:
            return items

        return {(object_id if element_type is None else Util.cast(element, element_type)): element
                for object_id, element in (
            items.items() if isinstance(items, dict)
            else enumerate(items)
        )}

    @staticmethod
    def keys(items: Union[dict, list]) -> list:
        """Get element keys or list indices."""

        return list(items.keys()) if isinstance(items, dict) else list(range(len(items)))

    @staticmethod
    def set_to_csv(items: Set[Union[int, str, float]], sep=',', empty_as_none=True) -> str:
        """join elements as a single string with some separator"""

        return (str.join(sep, [str(t_id) for t_id in items]) if len(items) > 0
                else (None if empty_as_none else ''))

    @staticmethod
    def csv_to_set(items: Optional[str], sep=',', item_type=None, empty_as_none=False) -> Tuple[set,str]:
        """join elements as a single string with some separator"""

        items_list = []
        if items is not None:
            items_list = items.split(sep)
            if item_type is not None:
                items_list = [item_type(item) for item in items_list]

        # unique values
        n_items = len(items_list)
        unique_items = list(dict.fromkeys(items_list))
        warning = None
        if len(unique_items) < n_items:
            warning = "Some duplicated elements have been removed"

        return set(unique_items) if len(unique_items) > 0 else (None if empty_as_none else set()), warning


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

        self.spec: PhaseSpecification = PhaseSpecification({
                "tasks": [],
                "shared_blocks": [],
                "communications": [],
                "ranks": {}
            })
        """The specification to edit"""

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
                self.__prompt.print_info("You can also enter the interactive mode by adding the --interactive argument")
                raise SystemExit(1)

            if self.__args.spec_file is None:
                self.__prompt.print_error("The `spec-file` argument is required")
                self.__prompt.print_info("You can also enter the interactive mode by adding the --interactive argument")
                raise SystemExit(1)

        spec = None
        if self.__args.spec_file:
            spec = self.load_spec_from_file(self.__args.spec_file)

        if spec:
            self.spec = spec

        return self.spec

    def build(self):
        """Build the data set"""

        data_stem = self.__args.data_stem
        if self.__args.interactive is not False:
            data_stem = self.__prompt.prompt(
                "Data stem ?",
                default=(os.path.join(PROJECT_PATH, "output", "maker", "data",
                                      self.__datetime.strftime("%y%m%d%H%M%S"), "data")
                         ) if self.__args.data_stem is None else self.__args.data_stem
            )

        # create and populate phase
        phase = Phase(self.__logger, 0)
        phase.populate_from_specification(self.spec)
        # Save
        writer_parameters: dict = {
            "compressed": self.__args.compressed,
            "json_output_suffix": "json",
        }

        output_dir = f"{os.sep}".join(data_stem.split(os.sep)[:-1])
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        writer = VTDataWriter(self.__logger, None, data_stem, writer_parameters)
        writer.write({phase.get_id(): phase})
        self.__prompt.print_success("Dataset has been generated.")

        self.__args.data_stem = data_stem

    def load_sample(self, use_explicit_keys: bool = False):
        """Create a new sample specification as represented by diagram specified in issue #506
        This method implementation indicates also how to create a specification from Python code
        """

        spec = PhaseSpecification({
            "tasks": [
                TaskSpecification({
                    "collection_id": 0,
                    "time": 2.0
                }),
                TaskSpecification({
                    "collection_id": 0,
                    "time": 3.5
                }),
                TaskSpecification({
                    "collection_id": 0,
                    "time": 5.0
                })
            ],
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
            spec["tasks"] = {comm_id: comm for comm_id, comm in enumerate(spec["tasks"])}
            spec["communications"] = {task_id: task for task_id, task in enumerate(spec["communications"])}
            spec["shared_blocks"] = {block_id: block for block_id, block in enumerate(spec["shared_blocks"])}

        self.spec = spec

    def load_spec_from_file(self, file_path) -> Optional[PhaseSpecificationNormalizer]:
        """Load a specification from a file (Yaml or Json)

        Return a PhaseSpecificationNormalizer instance on success or None on failure.
        Exit the program if specification file is invalid in non-interactive mode
        """

        if not os.path.isfile(file_path):
            raise FileNotFoundError("File not found")

        spec = PhaseSpecification()
        with open(file_path, "r", encoding="utf-8") as file_stream:
            if file_path.endswith(".json"):
                spec_dict = json.load(file_stream)
                # in json keys are strings (int not supported by the JSON format) so apply casts as needed
                if "ranks" in spec_dict:
                    spec_dict["ranks"] = {int(rank_id): data for rank_id, data in spec_dict["ranks"].items()}
            else:
                spec_dict = yaml.safe_load(file_stream)

        try:
            spec = PhaseSpecificationNormalizer().denormalize(spec_dict)
            # try load phase to validate input file
            Phase(self.__logger, 0).populate_from_specification(spec, self.__args.multiple_sharing is not False)
        except RuntimeError as e:
            self.__prompt.print_error(f"Input specification error: {e}")
            if self.__args.interactive is False:
                raise SystemExit(-1) from e
            spec = None

        return spec

    def print(self, output_format: str = "json"):
        """print a specification to the console"""

        normalized_spec = PhaseSpecificationNormalizer().normalize(self.spec)

        if output_format == "json":
            print("----------- BEGIN JSON -----------")
            print(json.dumps(normalized_spec, sort_keys=True, indent=2, separators=(',', ": ")))
            print("----------- END JSON -------------")
        elif output_format == "yaml":
            print("----------- BEGIN YAML -----------")
            print(yaml.dump(normalized_spec, indent=2, Dumper=YamlSpecificationDumper, default_flow_style=None))
            print("----------- END YAML -------------")
        else:
            print(self.spec)

    def ask_object(self, objects: Union[dict, list], object_type_name: str, can_add: bool = False,
                   can_go_back=False, question: str = None, validate: Optional[Callable] = None, default=None, ):
        """Request user to select a choice in a list of dict keys or list indices"""

        choices = Util.keys(objects)
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
        """Create or update an object in a list (id is the index) or in a dict (id is the key) for interactive input
        of tasks, communications and shared blocks"""

        object_id = self.ask_object(parent, object_type_name, True, can_go_back=True)

        if object_id == "*Back":
            return

        # retrieve current value
        object_data = (default if object_id == "*New" else parent[object_id])
        object_data = update(object_data, None if object_id == "*New" else object_id)

        is_new = False
        if object_id == "*New":
            is_new = True
            if isinstance(parent, dict):
                # default is for new object is max key + 1
                object_id = max(parent.keys(), default=-1) + 1
                object_id = self.__prompt.prompt(
                    f"{object_type_name.capitalize()} id ?", required=True, value_type=int, default=object_id,
                    validate=lambda t_id: f"{object_type_name.capitalize()} with id already exists. Please choose another id !"
                    if t_id in parent.keys()
                    else None)
            else:
                # no explicit id for list item as index is used
                object_id = None

        # append or update object in or to the parent list or dict
        if isinstance(parent, dict):
            parent[object_id] = object_data
        else:
            if object_id is not None:
                parent[object_id] = object_data  # update
            else:
                object_id = len(parent)
                parent.append(object_data)  # create

        self.__prompt.print_info(f"{object_type_name.capitalize()} with id {object_id} has been "
                                 f"{'added' if is_new else 'updated'} succesfully")

    def make_task(self):
        """Creates or updates a task in interactive mode"""

        self.make_object(
            self.spec.get("tasks"),
            "task",
            default=TaskSpecification({"collection_id": 0, "time":0.0}),
            update=lambda task, t_id: self.update_task(task)
        )

    def update_task(self, task: TaskSpecification):
        """Ask for task time, collection_id in interactive mode"""

        task["time"] = self.__prompt.prompt("Task time ?", required=True, value_type=float,
                                                            default=task.get("time", 0.0))
        collection_id = self.__prompt.prompt("Collection id ?", required=True, value_type=int,
                                                            default=task.get("collection_id", 7))
        task["collection_id"] = collection_id

        return task

    def update_communication(self, comm):
        """Ask for communication size, from and to in interactive mode"""

        tasks: Union[dict, list] = self.spec["tasks"]

        comm["size"] = self.__prompt.prompt(
            "Communication size ?", required=True, value_type=float, default=comm.get("size", 0.0))
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

    def make_communication(self):
        """Creates or updates a communication in interactive mode"""

        self.make_object(
            self.spec.get("communications"),
            "communication",
            default=CommunicationSpecification({"size": 0.0}),
            update=lambda comm, comm_id: self.update_communication(comm)
        )

    def update_shared_block(self, block):
        """Ask for shared block size, and tasks in interactive mode"""

        tasks = self.spec["tasks"]
        ranks = self.spec["ranks"]
        block["size"] = self.__prompt.prompt(
            "Shared block size ?", required=True, value_type=float, default=block.get("size", 0.0))

        tasks_valid = False
        all_tasks = Util.keys(tasks)
        block_task_ids = Util.keys(block["tasks"])
        while not tasks_valid:
            tasks_valid = True
            task_ids = self.__prompt.prompt("Shared block tasks ids (comma separated) ?", required=False,
                                            value_type=str, default=Util.set_to_csv(block_task_ids))
            if task_ids is None or task_ids == '':
                block["tasks"] = []
                return block

            try:
                task_ids, warning = Util.csv_to_set(task_ids, item_type=int)
                if warning is not None:
                    self.__prompt.print_warning(warning)
            except ValueError as ex:
                self.__prompt.print_error(f"Input error: {ex.args[0]}")
                tasks_valid = False
                continue

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

    def make_shared_block(self):
        """Creates or updates a communication in interactive mode"""

        self.make_object(
            self.spec.get("shared_blocks"),
            "shared block",
            default=SharedBlockSpecification({"size": 0.0, "tasks": [], "home_rank": None}),
            update=lambda block, block_id: self.update_shared_block(block)
        )

    def update_rank(self, rank: RankSpecification, rank_id: Optional[int]):
        """Ask for rank id (if new) and tasks in interactive mode"""

        all_tasks = Util.keys(self.spec["tasks"])
        rank_task_ids = rank["tasks"]
        valid = False
        while not valid:
            valid = True
            task_ids_csv = self.__prompt.prompt("Rank tasks (comma separated) ?",
                                                required=False, value_type=str, default=Util.set_to_csv(rank_task_ids))
            try:
                task_ids, warning = Util.csv_to_set(task_ids_csv, item_type=int)
                if warning is not None:
                    self.__prompt.print_warning(warning)
            except ValueError as ex:
                self.__prompt.print_error(f"Input error: {ex.args[0]}")
                valid = False
                continue

            for t in task_ids:
                if not t in all_tasks:
                    self.__prompt.print_error(f"Task {t} not found")
                    valid = False
                    break
                for r_id, r in self.spec["ranks"].items():
                    if rank_id != r_id and t in r["tasks"]:
                        self.__prompt.print_error(f"Task {t} already defined on rank {r_id}")
                        valid = False
                        break
                if not valid:
                    break

            rank["tasks"] = task_ids
        return rank

    def make_rank(self):
        """Creates or updates a rank in interactive mode"""

        self.make_object(
            self.spec["ranks"],
            "rank",
            default=RankSpecification({"tasks": []}),
            update=self.update_rank
        )

    def remove_task(self):
        """Remove a task in interactive mode"""

        choice = self.ask_object(self.spec["tasks"], "task", False, can_go_back=True)
        if choice == "*Back":
            return

        # List communications from/to the task
        t_communications: dict = {}
        for c_id, communication in Util.to_dict(self.spec["communications"]).items():
            if communication["from"] == choice or communication["to"] == choice:
                t_communications[c_id] = communication

        # Find task shared block(s)
        t_orphan_shared_blocks: dict = {}
        for b_id, block in Util.to_dict(self.spec["shared_blocks"]).items():
            if choice in block["tasks"] and len(block["tasks"]) == 1:
                t_orphan_shared_blocks[b_id] = block

        # Find task rank
        t_rank_id = None
        for r_id, rank in self.spec["ranks"].items():
            if choice in rank["tasks"]:
                t_rank_id = r_id

        messages = []
        if t_rank_id is not None:
            messages.append(f"Task will be removed from rank {t_rank_id}.")
        if len(t_communications) > 0:
            messages.append("The following communications will be removed: " + str(t_communications))
        if len(t_orphan_shared_blocks) > 0:
            messages.append("The following shared block won't be linked to any task: " +
                            str(t_orphan_shared_blocks))

        if len(messages) > 0:
            self.__prompt.print_warning(str.join(f"{os.linesep}", messages))

        confirm_choice = self.__prompt.prompt("Are you sure ?",
                                              choices=["Yes", "No"],
                                              required=True, default="No")

        if confirm_choice == "Yes":
            # Delete communications
            for c in t_communications:
                del self.spec["communications"][c]
            # Remove from rank
            if t_rank_id is not None:
                self.spec["ranks"][t_rank_id]["tasks"] = list(filter(lambda item: item != choice,
                                                                self.spec["ranks"][t_rank_id]["tasks"]))
            # Delete task
            del self.spec["tasks"][int(choice)]

    def remove_rank(self):
        """Remove a shared block in interactive mode"""

        choice = self.ask_object(self.spec["ranks"], "rank", False, can_go_back=True)
        if choice == "*Back":
            return

        messages = []
        # Prevent rank removal if a task is still in that rank
        rank_tasks = self.spec["ranks"][choice]["tasks"]
        if len(rank_tasks) > 0:
            messages.append(
                f"Tasks with ids { Util.set_to_csv(rank_tasks, sep=', ') } no more belong to a rank")

        # Prevent rank removal if a shared block home rank is that rank
        if len(self.spec["shared_blocks"]) > 0:
            b_ids = []
            for b_id, block in Util.to_dict(self.spec["shared_blocks"]).items():
                if block["home_rank"] == choice:
                    b_ids.append(b_id)
            if len(b_ids) > 0:
                messages.append(f"Shared block(s) with ids {Util.set_to_csv(b_ids, sep=', ')} "
                                "home rank will no longer be valid")

        if len(messages) > 0:
            self.__prompt.print_warning(str.join(f"{os.linesep}", messages))

        confirm_choice = self.__prompt.prompt("Are you sure ?",
                                              choices=["Yes", "No"],
                                              required=True, default="No")

        if confirm_choice == "Yes":
            # Delete task
            del self.spec["ranks"][int(choice)]

    def remove_shared_block(self):
        """Remove a shared block in interactive mode"""

        choice = self.ask_object(self.spec["shared_blocks"], "shared block", False, can_go_back=True)
        if choice == "*Back":
            return

        shared_block = Util.to_dict(self.spec["shared_blocks"])[choice]

        messages = []
        if len(shared_block['tasks']) > 0:
            messages.append(f"Tasks with ids {Util.set_to_csv(shared_block['tasks'], sep=', ')} are sharing that block.")

        if len(messages) > 0:
            self.__prompt.print_warning(str.join(f"{os.linesep}", messages))

        confirm_choice = self.__prompt.prompt("Are you sure ?",
                                              choices=["Yes", "No"],
                                              required=True, default="No")

        if confirm_choice == "Yes":
            # Delete chared block
            del self.spec["shared_blocks"][int(choice)]

    def remove_communication(self):
        """Remove a communication in interactive mode"""

        choice = self.ask_object(self.spec["communications"], "communication", False, can_go_back=True)
        if choice == "*Back":
            return

        confirm_choice = self.__prompt.prompt("Are you sure ?",
                                              choices=["Yes", "No"],
                                              required=True, default="No")

        if confirm_choice == "Yes":
            # Delete chared block
            del self.spec["communications"][int(choice)]

    def remove_element(self):
        """Remove element (task, rank, shared block or communication) in interactive mode"""

        element_type = self.__prompt.prompt("Choose Type ?",
                                            choices=["Task", "Rank", "Shared Block", "Communication", "*Back"],
                                            required=True, default=None)
        if element_type == "*Back":
            return
        elif element_type == "Task":
            self.remove_task()
        elif element_type == "Rank":
            self.remove_rank()
        elif element_type == "Shared Block":
            self.remove_shared_block()
        elif element_type == "Communication":
            self.remove_communication()

    def run_extra_action(self, action: str):
        """Run an extra action"""

        if action == "Extra: load sample":
            self.load_sample(use_explicit_keys=True)
            action = "Build"
        elif action == "Extra: print":
            frmt = self.__prompt.prompt("Format ?", choices=["yaml", "json", "python (debug)"], required=True, default="yaml")
            self.print(frmt)
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
                o_file.write(PhaseSpecificationNormalizer().normalize(self.spec), frmt)

    def run_action(self, action: str):
        """Run an action"""

        if action == "Make Task":
            self.make_task()
        elif action == "Make Rank":
            self.make_rank()
        elif action == "Make Shared block":
            self.make_shared_block()
        elif action == "Make Communication":
            if len(self.spec["tasks"]) < 2:
                self.__prompt.print_error("To create a communication please create at least 2 tasks")
                action = "Make Task"
            else:
                self.make_communication()
        elif action == "Remove Element":
            self.remove_element()
        elif action == "Build":
            try:
                self.build()
                action = "Extra: run"
            except RuntimeError as e:
                self.__prompt.print_error(e.args[0])
        elif action == "Extra: load file":
            file_path = self.__prompt.prompt("File path (Yaml or Json) ?", required=True)
            self.load_spec_from_file(file_path)
        elif action == "Extra: run":
            self.__args.config_file = self.__prompt.prompt("LBAF Configuration file ?", required=True,
                                                           default=self.__args.config_file)

            if not os.path.exists(self.__args.config_file):
                self.__prompt.print_error(f"File not found at {self.__args.config_file}.")
            else:
                subprocess.run(["python", f"{PROJECT_PATH}/src/lbaf", "-c", self.__args.config_file], check=True)
        else:
            self.run_extra_action(action)

    def run(self):
        """Run the JSONDatasetMaker"""

        # Parse command line arguments
        self.__parse_args()

        self.spec = self.process_args()

        # Build immediately in non interactive mode
        if self.__args.interactive is False:
            self.build()

        if self.__args.interactive is False:
            return

        # Consider False value as True (e.g. None) for interactive mode
        self.__args.interactive = True

        # Loop on interactive mode available actions
        action: str = "Make Task"  # default action is a sample
        while action != "Build JSON file":
            action = self.__prompt.prompt(
                "Choose an action ?",
                choices=[
                    "Make Task",
                    "Make Rank",
                    "Make Shared block",
                    "Make Communication",
                    "Remove Element",
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
                    self.run_action(action)
                # Catch any exception so that only the user can choose to exit the script (interactive) loop
                except Exception as err:  # pylint:disable=W0718:broad-exception-caught
                    self.__prompt.print_error(str(err.args[0]) if len(err.args) > 0
                                              else f"An error of type {type(err).__name__} has occured")


if __name__ == "__main__":
    JSONDataFilesMaker().run()
