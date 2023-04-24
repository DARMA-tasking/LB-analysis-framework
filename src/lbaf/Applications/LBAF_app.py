"""LBAF application module"""
import argparse
import os
import sys
import math
from typing import cast, List, Dict, Any, Union
from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError
import yaml

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as path_ex:
    print(f"Can not add project path to system path. Exiting.\nERROR: {path_ex}")
    raise SystemExit(1) from path_ex

# pylint: disable=C0413
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.colors import green
from lbaf.Utils.functions import abspath_from
# pylint: enable=C0413

def get_config_file_path() -> str:
    """Parse command line argument and return config file path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config file.", default="conf.yaml")
    args = parser.parse_args()
    if args.config:
        # try to search the file from this place
        config_file = os.path.abspath(args.config)
        # if not found we might search in the config directory at project root
        # but some thing will be disturbing : in config files we have path that must be relative
        # to the current directory but then we might prefer paty to be relative to the configuration
        # file location
        if not os.path.isfile(config_file):
            config_dir = os.path.join(
                f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-4]), "config"
            )
            config_file = config_dir + '/' + args.config
    else:
        sys.excepthook = exc_handler
        raise FileNotFoundError("Please provide path to the config file with '--config' argument.")

    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"File not found at path {args.config}")
    return config_file


def check_and_get_schema_validator():
    """Ensure that SchemaValidator can be imported and is the latest available version."""
    module_name = green(f"[{os.path.splitext(os.path.split(__file__)[-1])[0]}]")

    def save_schema_validator_and_init_file(import_dir: str):
        with open(os.path.join(import_dir, "__init__.py"), "wt", encoding="utf-8") as init_file:
            init_file.write('\n')
        try:
            script_name = "JSON_data_files_validator.py"
            script_url = f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{script_name}"
            filename = urlretrieve(script_url, os.path.join(import_dir, script_name))
            print(f"{module_name} Saved SchemaValidator to: {filename}")
        except HTTPError as err:
            sys.excepthook = exc_handler
            raise ConnectionError(f"Can not download file: {err.filename} \n"
                                  f"Server responded with code: {err.fp.code} and message: {err.fp.msg}") from err
        except URLError as err:
            sys.excepthook = exc_handler
            raise ConnectionError("Probably there is no internet connection") from err

    overwrite_validator = True
    config_file = None
    if __name__ == "__main__":
        config_file = get_config_file_path()
        with open(config_file, "rt", encoding="utf-8") as config:
            conf = yaml.safe_load(config)
        overwrite_validator = conf.get("overwrite_validator", True)
    if overwrite_validator:
        import_dir = os.path.join(project_path, "lbaf", "imported")
        if not os.path.isdir(import_dir):
            os.makedirs(import_dir)
            save_schema_validator_and_init_file(import_dir=import_dir)
        else:
            save_schema_validator_and_init_file(import_dir=import_dir)
    else:
        print(f"{module_name} Option \'overwrite_validator\' in configuration file: {config_file} is set to False\n"
              f"{module_name} In case of `ModuleNotFoundError: No module named \'lbaf.imported\'` set it to True.")


check_and_get_schema_validator()

# pylint: disable=C0413
from lbaf import __version__
from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work
from lbaf.Execution.lbsRuntime import Runtime
from lbaf.IO.configurationValidator import ConfigurationValidator
from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.IO.lbsVisualizer import Visualizer
import lbaf.IO.lbsStatistics as lbstats
from lbaf.Model.lbsPhase import Phase
from lbaf.Utils.logger import logger
# pylint: enable=C0413

class InternalParameters:
    """Represent LBAF application parameters"""
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

    def __init__(self, config_file: str):
        config = self.load_config(from_file=config_file)
        config_dir = os.path.dirname(config_file)

        # Initialize logger
        lvl = cast(str, config.get("logging_level", "info"))
        self.logger = logger(
            name="lbaf",
            level=lvl,
            theme=config.get("terminal_background", None),
            log_to_console=config.get("log_to_file", None) is None,
            log_to_file=abspath_from(config.get("log_to_file", None), config_dir)
        )
        self.logger.info("Logging level: %s", lvl.lower())

        # Initialize and check configuration
        self.validate_configuration(config)
        self.init_parameters(config, config_dir)
        self.check_parameters()

        # Print startup information
        self.logger.info("Executing LBAF version %s", __version__)
        svi = sys.version_info
        self.logger.info(
            "Executing with Python %s.%s.%s", svi.major, svi.minor, svi.micro)

    def load_config(self, from_file: str)-> dict:
        """Check extension, read YML file and return parsed YAML configuration file"""
        if os.path.splitext(from_file)[-1] in [".yml", ".yaml"] and os.path.isfile(from_file):
            # Try to open configuration file
            logger().info("Found configuration file %s", from_file)
            try:
                with open(from_file, "rt", encoding="utf-8") as config:
                    self.configuration_file_found = True
                    return yaml.safe_load(config)
            except yaml.MarkedYAMLError as err:
                logger().error(
                    "Invalid YAML file %s in line %s (%s) %s",
                    from_file, err.problem_mark.line if err.problem_mark is not None else -1, err.problem, err.context
                )
                sys.excepthook = exc_handler
                raise SystemExit(1) from err
        else:
            logger().error("Configuration file in %s not found", from_file)
            sys.excepthook = exc_handler
            raise SystemExit(1)

    def validate_configuration(self, config: dict):
        """Configuration file validation."""
        ConfigurationValidator(
            config_to_validate=config, logger=self.logger).main()

    def init_parameters(self, config: dict, config_dir: str):
        """Execute when YAML configuration file was found and checked"""
        # Get top-level allowed configuration keys
        self.__allowed_config_keys = cast(list, ConfigurationValidator.allowed_keys())

        # Assign parameters found in configuration file
        for param_key, param_val in config.items():
            if param_key in self.__allowed_config_keys:
                self.__dict__[param_key] = param_val

        # Parse visualizer parameters when available
        if (viz := config.get("LBAF_Viz")) is not None:
            # Retriveve mandatory visualization parameters
            try:
                self.grid_size = []
                for key in ("x_ranks", "y_ranks", "z_ranks"):
                    self.grid_size.append(viz[key])
                self.object_jitter = viz["object_jitter"]
                self.rank_qoi = viz["rank_qoi"]
                self.object_qoi = viz.get("object_qoi")
            except Exception as ex:
                self.logger.error("Missing visualizer configuration parameter(s): %s", ex)
                sys.excepthook = exc_handler
                raise SystemExit(1) from ex

            # Verify grid size consistency
            if math.prod(self.grid_size) < self.n_ranks:
                self.logger.error("Grid size: %s < %s", self.grid_size, self.n_ranks)
                sys.excepthook = exc_handler
                raise SystemExit(1)

            # Retrieve optional parameters
            self.save_meshes = viz.get("save_meshes", False)
            self.continuous_object_qoi = viz.get("force_continuous_object_qoi", False)
        else:
            # No visualization quantities of interest
            self.rank_qoi = self.object_qoi = self.grid_size = None

        # Parse data parameters if present
        if config.get("from_data") is not None:
            self.data_stem = config.get("from_data").get("data_stem")
            # # get data directory (because data_stem includes file prefix)
            data_dir = f"{os.sep}".join(self.data_stem.split(os.sep)[:-1])
            file_prefix = self.data_stem.split(os.sep)[-1]
            data_dir = abspath_from(data_dir, config_dir)
            self.data_stem = f"{os.sep}".join([data_dir, file_prefix])
            self.logger.info("Data stem: %s", self.data_stem)
            if isinstance(config.get("from_data", {}).get("phase_ids"), str):
                range_list = list(map(int, config.get("from_data").get("phase_ids").split('-')))
                self.phase_ids = list(range(range_list[0], range_list[1] + 1))
            else:
                self.phase_ids = config.get("from_data").get("phase_ids")

        # Parse sampling parameters if present
        if config.get("from_samplers") is not None:
            self.n_objects = config.get("from_samplers").get("n_objects", {})
            self.n_mapped_ranks = config.get("from_samplers").get("n_mapped_ranks")
            self.communication_degree = config.get("from_samplers").get("communication_degree")
            self.load_sampler = config.get("from_samplers").get("load_sampler")
            self.volume_sampler = config.get("from_samplers").get("volume_sampler")

        # Set output directory, local by default
        self.output_dir = abspath_from(config.get("output_dir", '.'), config_dir)

        # Parse JSON writer parameters when available
        self.json_params = {}
        if (wrt_json := config.get("write_JSON")) is not None:
            # Retrieve mandatory writer parameters
            try:
                self.json_params["compressed"] = wrt_json["compressed"]
            except Exception as ex:
                self.logger.error("Missing JSON writer configuration parameter(s): %s", ex)
                sys.excepthook = exc_handler
                raise SystemExit(1) from ex

            # Retrieve optional parameters
            self.json_params[
                "json_output_suffix"] = wrt_json.get("suffix", "json")
            self.json_params[
                "communications"] = wrt_json.get("communications", False)
            self.offline_LB_compatible = wrt_json.get(
                "offline_LB_compatible", False)

    def check_parameters(self):
        """Checks after initialization."""
        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)

class LBAFApp:
    """LBAF application class"""
    def __init__(self):
        # Retrieve configuration file path
        self.config_file = get_config_file_path()

        # Instantiate parameters
        self.__parameters = InternalParameters(config_file=self.config_file)

        # Assign logger to variable
        self.__logger = self.__parameters.logger

        # Create VT writer except when explicitly turned off
        self.json_writer = VTDataWriter(
            self.__logger,
            self.__parameters.output_dir,
            self.__parameters.output_file_stem,
            self.__parameters.json_params) if self.__parameters.json_params else None

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

    def main(self):
        """LBAFApp entrypoint to run"""
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
                objects, alpha, beta, gamma, self.__parameters.n_ranks
            )
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
        rebalanced_phase = runtime.execute(
            self.__parameters.algorithm.get("phase_id", -1))

        # Instantiate phase to VT file writer when requested
        if self.json_writer:
            if self.__parameters.offline_LB_compatible:
                self.__logger.info(
                    "Writing all phases to JSON files for offline load-balancing compatibility")
                self.json_writer.write(phases)
            else:
                print(phases)
                print(rebalanced_phase)
                self.__logger.info(f"Writing single phase {phase_id} to JSON files")
                self.json_writer.write([rebalanced_phase])

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


if __name__ == "__main__":
    LBAFApp().main()
