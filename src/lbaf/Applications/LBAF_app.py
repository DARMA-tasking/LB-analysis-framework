"""LBAF Application"""

import argparse
import os
import sys
import math
from typing import cast, Any, Dict, Union

import yaml

from lbaf import __version__, PROJECT_PATH

from lbaf.Applications import JSON_data_files_validator_loader
from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.path import abspath
from lbaf.Utils.logging import get_logger, Logger
import lbaf.IO.lbsStatistics as lbstats
from lbaf.IO.lbsConfigurationValidator import ConfigurationValidator
from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.IO.lbsVisualizer import Visualizer
from lbaf.Model.lbsPhase import Phase
from lbaf.Execution.lbsRuntime import Runtime


class InternalParameters:
    """Represent the parameters used internally by a a LBAF Application"""

    __logger: Logger
    n_ranks: int
    check_schema: bool
    output_dir: str
    output_file_stem: str
    file_suffix: str
    algorithm: Dict[str,Any]
    work_model: Dict[str,dict]
    rank_qoi: Union[str,None]
    object_qoi: Union[str,None]
    grid_size: Union[list,None]
    json_writer: Union[VTDataWriter,None]

    # from_samplers options
    n_objects: int
    n_mapped_ranks: int
    communication_degree: int
    load_sampler: dict
    volume_sampler: dict

    def __init__(self, config: dict, base_dir: str, logger: Logger):
        self.__logger = logger

        # Initialize and check configuration
        self.validate_configuration(config)
        self.init_parameters(config, base_dir)
        self.check_parameters()

        # Print startup information
        self.__logger.info(f"Executing LBAF version {__version__}")
        svi = sys.version_info #pylint: disable=W0612
        self.__logger.info(f"Executing with Python {svi.major}.{svi.minor}.{svi.micro}")

    def validate_configuration(self, config: dict):
        """Configuration file validation."""
        ConfigurationValidator(
            config_to_validate=config, logger=self.__logger).main()

    def init_parameters(self, config: dict, base_dir: str):
        """Execute when YAML configuration file was found and checked"""

        # Get top-level allowed configuration keys
        self.__allowed_config_keys = cast(list, ConfigurationValidator.allowed_keys())

        # Assign parameters found in configuration file
        for param_key, param_val in config.items():
            if param_key in self.__allowed_config_keys:
                self.__dict__[param_key] = param_val

        # Parse visualizer parameters when available
        if (viz := config.get("LBAF_Viz")) is not None:
            # Retrieve mandatory visualization parameters
            try:
                self.grid_size = []
                for key in ("x_ranks", "y_ranks", "z_ranks"):
                    self.grid_size.append(viz[key])
                self.object_jitter = viz["object_jitter"]
                self.rank_qoi = viz["rank_qoi"]
                self.object_qoi = viz.get("object_qoi")
            except Exception as e:
                self.__logger.error(f"Missing LBAF-Viz configuration parameter(s): {e}")
                sys.excepthook = exc_handler
                raise SystemExit(1) from e

            # Verify grid size consistency
            if math.prod(self.grid_size) < self.n_ranks:
                self.__logger.error("Grid size: {self.grid_size} < {self.n_ranks}")
                sys.excepthook = exc_handler
                raise SystemExit(1)

            # Retrieve optional parameters
            self.save_meshes = viz.get("save_meshes", False)
            self.continuous_object_qoi = viz.get("force_continuous_object_qoi", False)
        else:
            # No visualization quantities of interest
            self.rank_qoi = self.object_qoi = self.grid_size = None

        # Parse data parameters if present
        from_data = config.get("from_data")
        if from_data is not None:
            self.data_stem = from_data.get("data_stem")
            # # get data directory (because data_stem includes file prefix)
            data_dir = f"{os.sep}".join(self.data_stem.split(os.sep)[:-1])
            file_prefix = self.data_stem.split(os.sep)[-1]
            data_dir = abspath(data_dir, relative_to=base_dir)
            self.data_stem = f"{os.sep}".join([data_dir, file_prefix])
            self.__logger.info(f"Data stem: {self.data_stem}")
            if isinstance(from_data.get("phase_ids"), str):
                range_list = list(map(int, from_data.get("phase_ids").split('-')))
                self.phase_ids = list(range(range_list[0], range_list[1] + 1))
            else:
                self.phase_ids = from_data.get("phase_ids")

        # Parse sampling parameters if present
        from_samplers = config.get("from_samplers")
        if from_samplers is not None:
            self.n_objects = from_samplers.get("n_objects", {})
            self.n_mapped_ranks = from_samplers.get("n_mapped_ranks")
            self.communication_degree = from_samplers.get("communication_degree")
            self.load_sampler = from_samplers.get("load_sampler")
            self.volume_sampler = from_samplers.get("volume_sampler")

        # Set output directory, local by default
        self.output_dir = abspath(config.get("output_dir", '.'), relative_to=base_dir)

        # Parse JSON writer parameters when available
        self.json_params = {}
        if (wrt_json := config.get("write_JSON")) is not None:
            # Retrieve mandatory writer parameters
            try:
                self.json_params["compressed"] = wrt_json["compressed"]
            except Exception as e:
                self.__logger.error("Missing JSON writer configuration parameter(s): %s", e)
                sys.excepthook = exc_handler
                raise SystemExit(1) from e

            # Retrieve optional parameters
            self.json_params[
                "json_output_suffix"] = wrt_json.get("suffix", "json")
            self.json_params[
                "communications"] = wrt_json.get("communications", False)
            self.json_params[
                "offline_LB_compatible"] = wrt_json.get(
                "offline_LB_compatible", False)

    def check_parameters(self):
        """Checks after initialization."""

        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)

class Application:
    """LBAF application class."""

    __logger: Logger
    __parameters: InternalParameters
    json_writer: VTDataWriter

    """LBAF application class."""
    def __init__(self):
        # Init logger to instance variable. Initially the root logger.
        self.__logger = get_logger()

    def __configure(self, path: str):
        """Configure the application using the configuration file at the given path"""
        if os.path.splitext(path)[-1] in [".yml", ".yaml"]:
            # Try to open configuration file in read+text mode
            try:
                with open(path, "rt", encoding="utf-8") as file_io:
                    data = yaml.safe_load(file_io)
                    if not data.get("overwrite_validator", True):
                        self.__logger.info(
                            f"Option 'overwrite_validator' in configuration file: {path} is set to False"
                        )
            except yaml.MarkedYAMLError as err:
                err_line = err.problem_mark.line if err.problem_mark is not None else -1
                self.__logger.error(
                    f"Invalid YAML file {path} in line {err_line} ({err.problem}) {err.context}"
                )
                sys.excepthook = exc_handler
                raise SystemExit(1) from err
        else:
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Change logger (with parameters from the configuration data)
        lvl = cast(str, data.get("logging_level", "info"))
        config_dir = os.path.dirname(path)
        log_to_file = data.get("log_to_file", None)
        self.__logger = get_logger(
            name="lbaf",
            level=lvl,
            theme=data.get("terminal_background", None),
            log_to_console=data.get("log_to_console", None) is None,
            log_to_file=None if log_to_file is None else abspath(data.get("log_to_file"), relative_to=config_dir)
        )
        self.__logger.info(f"Logging level: {lvl.lower()}")
        if log_to_file is not None:
            self.__logger.info(f"Logging to file: {abspath(data.get('log_to_file'), relative_to=config_dir)}")

        # Instantiate the application internal parameters
        self.__parameters = InternalParameters(config=data, base_dir=os.path.dirname(path), logger=self.__logger)

        # Create VT writer except when explicitly turned off
        self.json_writer = VTDataWriter(
            self.__logger,
            self.__parameters.output_dir,
            self.__parameters.output_file_stem,
            self.__parameters.json_params) if self.__parameters.json_params else None

        return data

    def __get_config_path(self)-> str:
        """Find the config file from the '-configuration' command line argument and returns its absolute path
        (if configuration file path is relative it is searched in the current working directory and at the end in the
        {PROJECT_PATH}/config directory)

        :raises FileNotFoundError: if configuration file cannot be found
        """

        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("-c", "--configuration",
            help="Path to the config file. If path is relative it must be resolvable from either the current working "
                "directory or the config directory",
            default=None
        )
        args = parser.parse_args()
        path = None
        path_list = []

        if args.configuration is None:
            self.__logger.warning("No configuration file given. Fallback to default `conf.yaml` file in "
            "working directory or in the project config directory !")
            args.configuration = "conf.yaml"

        # search config file in the current working directory if relative
        path = abspath(args.configuration)
        path_list.append(path)
        if (
            path is not None and
            not os.path.isfile(path) and
            not os.path.isabs(args.configuration) and PROJECT_PATH is not None
        ):
            # then search config file relative to the config folder
            search_dir = abspath("config", relative_to=PROJECT_PATH)
            path = search_dir + '/' + args.configuration
            path_list.append(path)

        if not os.path.isfile(path):
            sys.excepthook = exc_handler
            error_message = "The configuration file cannot be found at\n"
            for invalid_path in path_list:
                error_message += " " + invalid_path + " -> not found\n"
            error_message += (
                "If you provide a relative path, please verify that the file exists relative to the "
                "current working directory or to the `config` directory"
            )
            raise FileNotFoundError(error_message)
        else:
            self.__logger.info(f"Found configuration file at path {path}")

        return path

    def run(self):
        """Runs the LBAF application"""
        # Find configuration file absolute path
        config_file = self.__get_config_path()

        # Apply configuration
        cfg = self.__configure(config_file)

        # Download JSON data files validator (JSON data files validator is required to continue)
        JSON_data_files_validator_loader.load(cfg.get("overwrite_validator", True))
        if not JSON_data_files_validator_loader.is_loaded():
            raise RuntimeError("The JSON data files validator must be loaded to run the application")

        # Initialize random number generator
        lbstats.initialize()

        # Create dictionary for phase instances
        phases = {}

        # Check schema
        check_schema = True if "check_schema" not in self.__parameters.__dict__ else self.__parameters.check_schema

        # Populate phase depending on chosen mechanism
        if self.__parameters.data_stem:
            # Populate phase from log files and store number of objects
            file_suffix = None if "file_suffix" not in self.__parameters.__dict__ else self.__parameters.file_suffix

            # Initializing reader
            if file_suffix is not None:
                reader = LoadReader(
                    file_prefix=self.__parameters.data_stem,
                    n_ranks=self.__parameters.n_ranks,
                    logger=self.__logger,
                    file_suffix=file_suffix,
                    check_schema=check_schema)
            else:
                reader = LoadReader(
                    file_prefix=self.__parameters.data_stem,
                    n_ranks=self.__parameters.n_ranks,
                    logger=self.__logger,
                    check_schema=check_schema)

            # Iterate over phase IDs
            for phase_id in self.__parameters.phase_ids:
                # Create a phase and populate it
                phase = Phase(
                    self.__logger, phase_id, reader=reader)
                phase.populate_from_log(phase_id)
                phases[phase_id] = phase
        else:
            # Pseudo-randomly populate a phase 0
            phase_id = 0
            phase = Phase(self.__logger, phase_id)
            phase.populate_from_samplers(
                self.__parameters.n_ranks,
                self.__parameters.n_objects,
                self.__parameters.load_sampler,
                self.__parameters.volume_sampler,
                self.__parameters.communication_degree,
                self.__parameters.n_mapped_ranks)
            phases[phase_id] = phase

        # Report on initial rank and edge statistics
        initial_phase = phases[min(phases.keys())]
        self.__print_statistics(initial_phase, "initial")

        # Perform brute force optimization when needed
        if "brute_force_optimization" in self.__parameters.__dict__ and self.__parameters.algorithm["name"] != "BruteForce":
            # Prepare input data for rank order enumerator
            self.__logger.info("Starting brute force optimization")
            objects = []

            # Iterate over ranks
            for rank in initial_phase.get_ranks():
                for o in rank.get_objects():
                    entry = {
                        "id": o.get_id(),
                        "load": o.get_load(),
                        "to": {},
                        "from": {}}
                    comm = o.get_communicator()
                    if comm:
                        for k, v in comm.get_sent().items():
                            entry["to"][k.get_id()] = v
                        for k, v in comm.get_received().items():
                            entry["from"][k.get_id()] = v
                    objects.append(entry)
            objects.sort(key=lambda x: x.get("id"))

            # Execute rank order enumerator and fetch optimal arrangements
            alpha, beta, gamma = [
                self.__parameters.work_model.get("parameters", {}).get(k)
                for k in ("alpha", "beta", "gamma")
            ]
            n_a, w_min_max, a_min_max = compute_min_max_arrangements_work(
                objects, alpha, beta, gamma, self.__parameters.n_ranks)
            if n_a != self.__parameters.n_ranks ** len(objects):
                self.__logger.error("Incorrect number of possible arrangements with repetition")
                sys.excepthook = exc_handler
                raise SystemExit(1)
            self.__logger.info(
                f"Minimax work: {w_min_max:4g} for {len(a_min_max)} optimal arrangements amongst {n_a}")
        else:
            self.__logger.info("No brute force optimization performed")
            a_min_max = []

        # Instantiate runtime
        runtime = Runtime(
            phases,
            self.__parameters.work_model,
            self.__parameters.algorithm,
            a_min_max,
            self.__logger,
            self.__parameters.rank_qoi if self.__parameters.rank_qoi is not None else '',
            self.__parameters.object_qoi if self.__parameters.object_qoi is not None else '')

        # Execute runtime for specified phases, -1 for all phases
        offline_LB_compatible = self.__parameters.json_params.get(
            "offline_LB_compatible", False)
        rebalanced_phase = runtime.execute(
            self.__parameters.algorithm.get("phase_id", -1),
            offline_LB_compatible)

        # Instantiate phase to VT file writer when requested
        if self.json_writer:
            if offline_LB_compatible:
                # Add rebalanced phase when present
                if not rebalanced_phase:
                    self.__logger.warning(
                        "No rebalancing took place for offline load-balancing")
                else:
                    # Determine if a phase with same index was present
                    if (existing_phase := phases.get(p_id := rebalanced_phase.get_id())):
                        # Apply object timings to rebalanced phase
                        self.__logger.info(
                            f"Phase {p_id} already present, applying its object loads to rebalanced phase")
                        original_loads = {
                            o.get_id(): o.get_load()
                            for o in phases[p_id].get_objects()}
                        for o in rebalanced_phase.get_objects():
                            o.set_load(original_loads[o.get_id()])

                    # Insert rebalanced phase into dictionary of phases
                    phases[p_id] = rebalanced_phase

                # Write all phases
                self.__logger.info(
                    f"Writing all ({len(phases)}) phases for offline load-balancing")
                self.json_writer.write(phases)
            else:
                self.__logger.info(f"Writing single phase {phase_id} to JSON files")
                self.json_writer.write(
                    {phase_id: rebalanced_phase})

        # Generate meshes and multimedia when requested
        if self.__parameters.grid_size:
            # Look for prescribed QOI bounds
            qoi_request = [self.__parameters.rank_qoi]
            qoi_request.append(
                self.__parameters.work_model.get(
                    "parameters").get(
                    "upper_bounds", {}).get(
                    self.__parameters.rank_qoi))
            qoi_request.append(self.__parameters.object_qoi)

            # Instantiate and execute visualizer
            visualizer = Visualizer(
                self.__logger,
                qoi_request,
                self.__parameters.continuous_object_qoi,
                phases,
                self.__parameters.grid_size,
                self.__parameters.object_jitter,
                self.__parameters.output_dir,
                self.__parameters.output_file_stem,
                runtime.get_distributions(),
                runtime.get_statistics())
            visualizer.generate(
                self.__parameters.save_meshes,
                not self.__parameters.rank_qoi is None)

        # Report on rebalanced phase when available
        if rebalanced_phase:
            l_stats = self.__print_statistics(rebalanced_phase, "rebalanced")
            with open(
                "imbalance.txt" if self.__parameters.output_dir is None
                else os.path.join(
                    self.__parameters.output_dir,
                    "imbalance.txt"), 'w', encoding="utf-8") as imbalance_file:
                imbalance_file.write(f"{l_stats.get_imbalance()}")

        # If this point is reached everything went fine
        self.__logger.info("Process completed without errors")

    def __print_statistics(self, phase: Phase, phase_name: str):
        """Print a set of rank and edge statistics"""

        # Print rank statistics
        l_stats = lbstats.print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_load(),
            f"{phase_name} rank load",
            self.__logger)
        lbstats.print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_max_object_level_memory(),
            f"{phase_name} rank object-level memory",
            self.__logger)
        lbstats.print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_size(),
            f"{phase_name} rank working memory",
            self.__logger)
        lbstats.print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_shared_memory(),
            f"{phase_name} rank shared memory",
            self.__logger)
        lbstats.print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_max_memory_usage(),
            f"{phase_name} maximum memory usage",
            self.__logger)

        # Print edge statistics
        lbstats.print_function_statistics(
            phase.get_edge_maxima().values(),
            lambda x: x,
            f"{phase_name} sent volumes",
            self.__logger)

        # Return rank load statistics
        return l_stats

if __name__ == "__main__":
    Application().run()
