"""LBAF Application"""

import argparse
import os
import sys
import math
from typing import cast, Any, Dict, List, Union

import yaml

from lbaf import __version__
from lbaf.Applications import JSON_data_files_validator_loader
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.common import abspath, is_editable
from lbaf.Utils.logging import get_logger, Logger
from lbaf.IO.lbsConfigurationValidator import ConfigurationValidator


class InternalParameters:
    """Represent the parameters used internally by a a LBAF Application"""

    logger: Logger
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
    write_vt: bool

    # from_samplers options
    n_objects: int
    n_mapped_ranks: int
    communication_degree: int
    load_sampler: dict
    volume_sampler: dict

    def __init__(self, config: dict, base_dir: str, logger: Logger):
        self.__logger = logger

        self.validate_configuration(config)
        self.init_parameters(config, base_dir)
        self.check_parameters()

        # Print startup information
        self.__logger.info(f"Executing LBAF version {__version__}")
        svi = sys.version_info #pylint: disable=W0612
        self.__logger.info("Executing with Python {svi.major}.{svi.minor}.{svi.micro}")

    def validate_configuration(self, config: dict):
        """Configuration file validation."""

        ConfigurationValidator(config_to_validate=config, logger=self.__logger).main()

    def init_parameters(self, config: dict, base_dir: str):
        """Execute when YAML configuration file was found and checked"""

        # Get top-level allowed configuration keys
        self.__allowed_config_keys = cast(list, ConfigurationValidator.allowed_keys())

        # Assign parameters found in configuration file
        for param_key, param_val in config.items():
            if param_key in self.__allowed_config_keys:
                self.__dict__[param_key] = param_val

        # Parse LBAF_Viz parameters when available
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
                self.__logger.error("Missing LBAF-Viz configuration parameter(s): {ex}")
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
            self.__logger.info("Data stem: {self.data_stem}")
            if isinstance(from_data.get("phase_ids"), str):
                range_list = list(map(int, from_data.get("phase_ids").split('-')))
                self.phase_ids = list(range(range_list[0], range_list[1] + 1))
            else:
                self.phase_ids = from_data.get("phase_ids")
        self.write_vt = config.get("write_vt", True)

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

    def check_parameters(self):
        """Checks after initialization."""

        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)

class Application:
    """LBAF Application class"""

    _logger: Logger
    params: InternalParameters

    def __init__(self):

        # Assign logger to instance variable. Default root logger.
        self._logger = get_logger()

    def __configure(self, path: str):
        """Configure the application using the configuration file at the given path"""

        if os.path.splitext(path)[-1] in [".yml", ".yaml"]:
            # Try to open configuration file in read+text mode
            try:
                with open(path, "rt", encoding="utf-8") as file_io:
                    data = yaml.safe_load(file_io)
                    if not data.get("overwrite_validator", True):
                        self._logger.info(
                            f"Option 'overwrite_validator' in configuration file: {path} is set to False"
                        )
            except yaml.MarkedYAMLError as err:
                err_line = err.problem_mark.line if err.problem_mark is not None else -1
                self._logger.error(
                    f"Invalid YAML file {path} in line {err_line} ({err.problem}) {err.context}"
                )
                sys.excepthook = exc_handler
                raise SystemExit(1) from err
        else:
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Initialize the application logger (with some parameters from the configuration data)
        lvl = cast(str, data.get("logging_level", "info"))
        config_dir = os.path.dirname(path)
        log_to_file = data.get("log_to_file", None)
        # change logger to a logger with some parameters found in configuration
        self._logger = get_logger(
            name="lbaf",
            level=lvl,
            theme=data.get("terminal_background", None),
            log_to_console=data.get("log_to_file", None) is None,
            log_to_file=None if log_to_file is None else abspath(data.get("log_to_file"), relative_to=config_dir)
        )
        self._logger.info(f"Logging level: {lvl.lower()}")

        # Instantiate the application internal parameters
        self.params = InternalParameters(config=data, base_dir=os.path.dirname(path), logger=self._logger)

        return data

    def __get_config_path(self)-> str:
        """Find the config file from the '-configuration' command line argument and returns its absolute path
        (if configuration file path is relative it is searched in the current working directory and at the end in the
        {project_dir}/config directory)

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
            self._logger.warning("No configuration file given. Fallback to default `conf.yaml` file in "
            "working directory or in the project config directory !")
            args.configuration = "conf.yaml"

        # search config file in the current working directory if relative
        path = abspath(args.configuration)
        path_list.append(path)
        if path is not None and not os.path.isfile(path) and not os.path.isabs(args.configuration) and is_editable():
            # then search config file relative to the config folder
            search_dir = abspath("../../../../config", relative_to=__file__)
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
            self._logger.info(f"Found configuration file at path {path}")

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

        # Imports depending on the JSON data files validator
        # pylint: disable=C0415
        from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work
        from lbaf.IO.lbsVTDataReader import LoadReader
        from lbaf.IO.lbsVTDataWriter import VTDataWriter
        from lbaf.Model.lbsPhase import Phase
        from lbaf.Execution.lbsRuntime import Runtime
        from lbaf.IO.lbsVisualizer import Visualizer
        import lbaf.IO.lbsStatistics as lbstats
        # pylint: enable=C0415

        # Initialize random number generator
        lbstats.initialize()

        # Create list of phase instances
        phases = [] #type: List[Phase]
        check_schema = True if "check_schema" not in self.params.__dict__ else self.params.check_schema
        if self.params.data_stem:
            file_suffix = None if "file_suffix" not in self.params.__dict__ else self.params.file_suffix

            # Initializing reader
            if file_suffix is not None:
                reader = LoadReader(
                    file_prefix=self.params.data_stem,
                    n_ranks=self.params.n_ranks,
                    logger=self._logger,
                    file_suffix=file_suffix,
                    check_schema=check_schema)
            else:
                reader = LoadReader(
                    file_prefix=self.params.data_stem,
                    n_ranks=self.params.n_ranks,
                    logger=self._logger,
                    check_schema=check_schema)

            # Populate phase from log files and store number of objects
            for phase_id in self.params.phase_ids:
                # Create a phase and populate it
                if file_suffix is not None:
                    phase = Phase(
                        self._logger, phase_id, file_suffix, reader=reader)
                else:
                    phase = Phase(
                        self._logger, phase_id, reader=reader)
                phase.populate_from_log(phase_id, self.params.data_stem)
                phases.append(phase)
        else:
            # Populate phase pseudo-randomly a phase 0
            phase = Phase(self._logger, 0)
            phase.populate_from_samplers(
                self.params.n_ranks,
                self.params.n_objects,
                self.params.load_sampler,
                self.params.volume_sampler,
                self.params.communication_degree,
                self.params.n_mapped_ranks)
            phases.append(phase)

        # Compute and print initial rank load and edge volume statistics
        curr_phase = phases[0]
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_load(),
            "initial rank load",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_object_level_memory(),
            "initial rank object-level memory",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_size(),
            "initial rank working memory",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_shared_memory(),
            "initial rank shared memory",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_memory_usage(),
            "initial maximum memory usage",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_edge_maxima().values(),
            lambda x: x,
            "initial sent volumes",
            self._logger)

        # Perform brute force optimization when needed
        if "brute_force_optimization" in self.params.__dict__ and self.params.algorithm["name"] != "BruteForce":
            # Prepare input data for rank order enumerator
            self._logger.info("Starting brute force optimization")
            objects = []

            # Iterate over ranks
            for rank in curr_phase.get_ranks():
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
                self.params.work_model.get("parameters", {}).get(k)
                for k in ("alpha", "beta", "gamma")
            ]
            n_a, w_min_max, a_min_max = compute_min_max_arrangements_work(
                objects, alpha, beta, gamma, self.params.n_ranks
            )
            if n_a != self.params.n_ranks ** len(objects):
                self._logger.error("Incorrect number of possible arrangements with repetition")
                sys.excepthook = exc_handler
                raise SystemExit(1)
            self._logger.info(
                f"Minimax work: {w_min_max:4g} for {len(a_min_max)} optimal arrangements amongst {n_a}"
            )
        else:
            self._logger.info("No brute force optimization performed")
            a_min_max = []

        # Instantiate and execute runtime
        runtime = Runtime(
            phases,
            self.params.work_model,
            self.params.algorithm,
            a_min_max,
            self._logger,
            self.params.rank_qoi if self.params.rank_qoi is not None else '',
            self.params.object_qoi if self.params.object_qoi is not None else '')
        runtime.execute()

        # Instantiate phase to VT file writer when requested
        if self.params.write_vt:
            vt_writer = VTDataWriter(
                curr_phase,
                self._logger,
                self.params.output_file_stem,
                output_dir=self.params.output_dir)
            vt_writer.write()

        # Generate meshes and multimedia when requested
        if self.params.grid_size:
            # Look for prescribed QOI bounds
            qoi_request = [self.params.rank_qoi]
            qoi_request.append(
                self.params.work_model.get(
                    "parameters").get(
                    "upper_bounds", {}).get(
                    self.params.rank_qoi))
            qoi_request.append(self.params.object_qoi)

            # Instantiate and execute visualizer
            ex_writer = Visualizer(
                self._logger,
                qoi_request,
                self.params.continuous_object_qoi,
                phases,
                self.params.grid_size,
                self.params.object_jitter,
                self.params.output_dir,
                self.params.output_file_stem,
                runtime.get_distributions(),
                runtime.get_statistics())
            ex_writer.generate(
                self.params.save_meshes,
                not self.params.rank_qoi is None
            )

        # Compute and print final rank load and edge volume statistics
        curr_phase = phases[-1]
        l_stats = lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_load(),
            "final rank loads",
            self._logger)
        with open(
            "imbalance.txt" if self.params.output_dir is None else os.path.join(
                self.params.output_dir, "imbalance.txt"), "w", encoding="utf-8") as imbalance_file:
            imbalance_file.write(
                f"{l_stats.get_imbalance()}") #pylint: disable=E1101
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_object_level_memory(),
            "final rank object-level memory",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_size(),
            "final rank working memory",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_shared_memory(),
            "final rank shared memory",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_memory_usage(),
            "final maximum memory usage",
            self._logger)
        lbstats.print_function_statistics(
            curr_phase.get_edge_maxima().values(),
            lambda x: x,
            "final sent volumes",
            self._logger)

        # Report on theoretically optimal statistics
        n_o = curr_phase.get_number_of_objects()
        ell = self.params.n_ranks * l_stats.get_average() / n_o #pylint: disable=E1101
        self._logger.info("Optimal load statistics for {n_o} objects with iso-time: {ell:6g}")
        q, r = divmod(n_o, self.params.n_ranks) #pylint: disable=C0103
        self._logger.info(
            f"\tminimum: {q * ell:6g}  maximum: {q + (1 if r else 0) * ell:6g}"
        )
        self._logger.info(
            f"\tstandard deviation: {ell * math.sqrt(r * (self.params.n_ranks - r)) / self.params.n_ranks:6g}"
            f" imbalance: {(self.params.n_ranks - r) / float(n_o):6g}" if r else '0'
        )

        # If this point is reached everything went fine
        self._logger.info("Process completed without errors")

if __name__ == "__main__":
    Application().run()
