"""LBAF application module"""
import argparse
import os
import sys
import math
from typing import cast, List, Dict, Any, Union, Tuple
import yaml

# append lbaf to path
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as path_ex:
    print(f"Can not add project path to system path. Exiting.\nERROR: {path_ex}")
    raise SystemExit(1) from path_ex

#pylint: disable=C0411,C0413
from lbaf import __version__
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.logger import logger
from lbaf.Utils.common import abspath_from
from lbaf.Applications.schema_validator_loader import check_and_get_schema_validator
#pylint: enable=C0411,C0413

try:
    import paraview.simple #pylint: disable=E0401,W0611
except: #pylint: disable=W0718,W0702
    pass

def parse_args() -> str:
    """Parses command line argument and resolve then return the input configuration file absolute path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configuration",
        help="Path to the config file. If path is relative it must be resolvable from either the current working "
            "directory or the config directory",
        default='conf.yaml'
    )
    args = parser.parse_args()
    path = None
    if args.configuration:
        # try to search the file from this place
        path = os.path.abspath(args.configuration)
        if path is not None and not os.path.isfile(path):
            # try to search the file relative to the config folder
            search_dir = os.path.join(
                f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-4]),
                "config"
            )
            path = search_dir + '/' + args.configuration
    else:
        sys.excepthook = exc_handler
        raise FileNotFoundError("Please provide path to the config file with '--configuration' argument.")

    if not os.path.isfile(path):
        sys.excepthook = exc_handler
        raise FileNotFoundError(
            f"Configuration file not found at path {args.config}."
            ' For relative paths, please make sure the file exists either in the current working directory or in'
            'the `config` directory'
        )
    else:
        logger().info(f"Found configuration file at path {path}")

    return path

def load_config(path: str)-> Tuple[dict, str]:
    """Loads and validate configuration file and returns the configuration dict and the name of the configuration
    directory"""
    if os.path.splitext(path)[-1] in [".yml", ".yaml"]:
        # Try to open configuration file in read+text mode
        try:
            with open(path, "rt", encoding="utf-8") as file_io:
                data = yaml.safe_load(file_io)
                if not data.get('overwrite_validator', True):
                    logger().info(
                        f"Option 'overwrite_validator' in configuration file: {path} is set to False"
                    )
        except yaml.MarkedYAMLError as err:
            err_line = err.problem_mark.line if err.problem_mark is not None else -1
            logger().error(
                f"Invalid YAML file {path} in line {err_line} ({err.problem}) {err.context}"
            )
            sys.excepthook = exc_handler
            raise SystemExit(1) from err
    else:
        sys.excepthook = exc_handler
        raise SystemExit(1)

    return data, os.path.dirname(path)

cfg, cfg_dir = {}, None
if __name__ == "__main__":
    # Parse input args
    config_file = parse_args()
    # Load configuration
    cfg, cfg_dir = load_config(config_file)
    # Download SchemaValidator script if overwrite
    check_and_get_schema_validator(cfg.get("overwrite_validator", True))

# Note that some of the following imports use the SchemaValidator so it is important that SchemaValidator
# is loaded at that point
# pylint: disable=C0412,C0413
from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work
from lbaf.Execution.lbsRuntime import Runtime
from lbaf.IO.configurationValidator import ConfigurationValidator
from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.IO.lbsVisualizer import Visualizer
import lbaf.IO.lbsStatistics as lbstats
from lbaf.Model.lbsPhase import Phase
# pylint: enable=C0412,C0413

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
    write_vt: bool

    # from_samplers options
    n_objects: int
    n_mapped_ranks: int
    communication_degree: int
    load_sampler: dict
    volume_sampler: dict

    def __init__(self, config: dict, base_dir: str):
        # init lbaf logger
        lvl = cast(str, config.get("logging_level", "info"))
        self.logger = logger(
            name="lbaf",
            level=lvl,
            theme=config.get("terminal_background", None),
            log_to_console=config.get("log_to_file", None) is None,
            log_to_file=abspath_from(config.get("log_to_file", None), base_dir)
        )
        self.logger.info("Logging level: %s", lvl.lower())

        self.validate_configuration(config)
        self.init_parameters(config, base_dir)
        self.check_parameters()

        # Print startup information
        self.logger.info("Executing LBAF version {__version__}")
        svi = sys.version_info #pylint: disable=W0612
        self.logger.info("Executing with Python {svi.major}.{svi.minor}.{svi.micro}")

    def validate_configuration(self, config: dict):
        """Configuration file validation."""
        ConfigurationValidator(config_to_validate=config, logger=self.logger).main()

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
            except Exception as ex:
                self.logger.error("Missing LBAF-Viz configuration parameter(s): {ex}")
                sys.excepthook = exc_handler
                raise SystemExit(1) from ex

            # Verify grid size consistency
            if math.prod(self.grid_size) < self.n_ranks:
                self.logger.error("Grid size: {self.grid_size} < {self.n_ranks}")
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
            data_dir = abspath_from(data_dir, base_dir)
            self.data_stem = f"{os.sep}".join([data_dir, file_prefix])
            self.logger.info("Data stem: {self.data_stem}")
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
        self.output_dir = abspath_from(config.get("output_dir", '.'), base_dir)

    def check_parameters(self):
        """Checks after initialization."""
        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)

class LBAFApp:
    """LBAF application class"""
    def __init__(self, config, base_dir):
        # Instantiate parameters
        self.params = InternalParameters(config=config, base_dir=base_dir)

        # Assign logger to variable
        self.logger = self.params.logger

    def main(self):
        """LBAFApp entrypoint to run"""
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
                    logger=self.logger,
                    file_suffix=file_suffix,
                    check_schema=check_schema)
            else:
                reader = LoadReader(
                    file_prefix=self.params.data_stem,
                    n_ranks=self.params.n_ranks,
                    logger=self.logger,
                    check_schema=check_schema)

            # Populate phase from log files and store number of objects
            for phase_id in self.params.phase_ids:
                # Create a phase and populate it
                if file_suffix is not None:
                    phase = Phase(
                        self.logger, phase_id, file_suffix, reader=reader)
                else:
                    phase = Phase(
                        self.logger, phase_id, reader=reader)
                phase.populate_from_log(phase_id, self.params.data_stem)
                phases.append(phase)
        else:
            # Populate phase pseudo-randomly a phase 0
            phase = Phase(self.logger, 0)
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
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_object_level_memory(),
            "initial rank object-level memory",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_size(),
            "initial rank working memory",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_shared_memory(),
            "initial rank shared memory",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_memory_usage(),
            "initial maximum memory usage",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_edge_maxima().values(),
            lambda x: x,
            "initial sent volumes",
            self.logger)

        # Perform brute force optimization when needed
        if "brute_force_optimization" in self.params.__dict__ and self.params.algorithm["name"] != "BruteForce":
            # Prepare input data for rank order enumerator
            self.logger.info("Starting brute force optimization")
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
                self.logger.error("Incorrect number of possible arrangements with repetition")
                sys.excepthook = exc_handler
                raise SystemExit(1)
            self.logger.info(
                f"Minimax work: {w_min_max:4g} for {len(a_min_max)} optimal arrangements amongst {n_a}"
            )
        else:
            self.logger.info("No brute force optimization performed")
            a_min_max = []

        # Instantiate and execute runtime
        runtime = Runtime(
            phases,
            self.params.work_model,
            self.params.algorithm,
            a_min_max,
            self.logger,
            self.params.rank_qoi if self.params.rank_qoi is not None else '',
            self.params.object_qoi if self.params.object_qoi is not None else '')
        runtime.execute()

        # Instantiate phase to VT file writer when requested
        if self.params.write_vt:
            vt_writer = VTDataWriter(
                curr_phase,
                self.logger,
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
                self.logger,
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
            self.logger)
        with open(
            "imbalance.txt" if self.params.output_dir is None else os.path.join(
                self.params.output_dir, "imbalance.txt"), 'w', encoding="utf-8") as imbalance_file:
            imbalance_file.write(
                f"{l_stats.get_imbalance()}") #pylint: disable=E1101
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_object_level_memory(),
            "final rank object-level memory",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_size(),
            "final rank working memory",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_shared_memory(),
            "final rank shared memory",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_max_memory_usage(),
            "final maximum memory usage",
            self.logger)
        lbstats.print_function_statistics(
            curr_phase.get_edge_maxima().values(),
            lambda x: x,
            "final sent volumes",
            self.logger)

        # Report on theoretically optimal statistics
        n_o = curr_phase.get_number_of_objects()
        ell = self.params.n_ranks * l_stats.get_average() / n_o #pylint: disable=E1101
        self.logger.info("Optimal load statistics for {n_o} objects with iso-time: {ell:6g}")
        q, r = divmod(n_o, self.params.n_ranks) #pylint: disable=C0103
        self.logger.info(
            "\tminimum: %s  maximum: %s",
            f"{q * ell:6g}",
            f"{q + (1 if r else 0) * ell:6g}"
        )
        self.logger.info(
            "\tstandard deviation: %s imbalance: %s",
            f"{ell * math.sqrt(r * (self.params.n_ranks - r)) / self.params.n_ranks:6g}",
            f"{(self.params.n_ranks - r) / float(n_o):6g}" if r else '0'
        )

        # If this point is reached everything went fine
        self.logger.info("Process completed without errors")


if __name__ == "__main__":
    LBAFApp(config=cfg, base_dir=cfg_dir).main()
