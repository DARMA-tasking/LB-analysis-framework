import argparse
import os
import sys
import logging
import math
import yaml
from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError


try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)
try:
    import paraview.simple
except:
    pass

from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.colors import green


def get_config_file() -> str:
    """ Parses command line argument and returns config file path. """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config file.")
    args = parser.parse_args()
    if args.config:
        config_file = os.path.abspath(args.config)
    else:
        sys.excepthook = exc_handler
        raise FileNotFoundError("Please provide path to the config file with '--config' argument.")

    return config_file


def check_and_get_schema_validator():
    """ Makes sure that SchemaValidator can be imported, and it's the latest version available.
    """
    module_name = green(f"[{os.path.splitext(os.path.split(__file__)[-1])[0]}]")

    def save_schema_validator_and_init_file(import_dir: str):
        with open(os.path.join(import_dir, "__init__.py"), 'wt') as init_file:
            init_file.write('\n')
        try:
            script_name = "JSON_data_files_validator.py"
            script_url = f"https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/{script_name}"
            filename, http_msg = urlretrieve(script_url, os.path.join(import_dir, script_name))
            print(f"{module_name} Saved SchemaValidator to: {filename}")
        except HTTPError as err:
            sys.excepthook = exc_handler
            raise ConnectionError(f"Can not download file: {err.filename} \n"
                                  f"Server responded with code: {err.fp.code} and message: {err.fp.msg}")
        except URLError as err:
            sys.excepthook = exc_handler
            raise ConnectionError("Probably there is no internet connection")

    overwrite_validator = True
    if __name__ == "__main__":
        config_file = get_config_file()
        with open(config_file, "rt") as config:
            conf = yaml.safe_load(config)
        overwrite_validator = conf.get("overwrite_validator", True)
    if overwrite_validator:
        import_dir = os.path.join(project_path, "lbaf", "imported")
        if not os.path.exists(import_dir):
            os.makedirs(import_dir)
            save_schema_validator_and_init_file(import_dir=import_dir)
        else:
            save_schema_validator_and_init_file(import_dir=import_dir)
    else:
        print(f"{module_name} Option 'overwrite_validator' in configuration file: {config_file} is set to False\n"
              f"{module_name} In case of `ModuleNotFoundError: No module named 'lbaf.imported'` set it to True.")


check_and_get_schema_validator()

from lbaf import __version__
from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work
from lbaf.Execution.lbsRuntime import Runtime
from lbaf.IO.configurationValidator import ConfigurationValidator
from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.IO.lbsMeshBasedVisualizer import MeshBasedVisualizer
import lbaf.IO.lbsStatistics as lbstats
from lbaf.Model.lbsPhase import Phase
from lbaf.Utils.logger import logger


class internalParameters:
    """A class to describe LBAF internal parameters
    """

    def __init__(self, config_file: str):
        # Starting logger
        self.logger = logger(conf=config_file)

        # Print startup information
        self.logger.info(f"Executing LBAF version {__version__}")
        sv = sys.version_info
        self.logger.info(f"Executing with Python {sv.major}.{sv.minor}.{sv.micro}")

        self.__allowed_config_keys = (
            "algorithm",
            "brute_force_optimization",
            "check_schema",
            "LBAF_Viz",
            "file_suffix",
            "from_data",
            "from_samplers",
            "logging_level",
            "log_to_file",
            "n_ranks",
            "output_dir",
            "output_file_stem",
            "overwrite_validator",
            "terminal_background",
            "work_model")

        # Read configuration values from file
        self.configuration_file_found = False
        self.configuration = self.get_configuration_file(conf_file=config_file)
        if self.configuration_file_found:
            self.configuration_validation()
            self.parse_conf_file()
        self.checks_after_init()

    def get_configuration_file(self, conf_file: str):
        """ Check extension, read YML file and return parsed YAML configuration file
        """
        if os.path.splitext(conf_file)[-1] in [".yml", ".yaml"] and os.path.isfile(conf_file):
            # Try to open configuration file
            self.logger.info(f"Found configuration file {conf_file}")
            try:
                with open(conf_file, "rt") as config:
                    self.configuration_file_found = True
                    return yaml.safe_load(config)
            except yaml.MarkedYAMLError as err:
                self.logger.error(f"Invalid YAML file {conf_file} in line {err.problem_mark.line} ({err.problem,} "
                                  f"{err.context})")
                sys.excepthook = exc_handler
                raise SystemExit(1)
        else:
            self.logger.error(f"Configuration file in {conf_file} not found")
            sys.excepthook = exc_handler
            raise SystemExit(1)

    def configuration_validation(self):
        """ Configuration file validation. """
        ConfigurationValidator(config_to_validate=self.configuration, logger=self.logger).main()

    def parse_conf_file(self):
        """ Execute when YAML configuration file was found and checked
        """
        # Assign parameters found in configuration file
        for param_key, param_val in self.configuration.items():
            if param_key in self.__allowed_config_keys:
                self.__dict__[param_key] = param_val

        # Parse LBAF_Viz parameters when available
        if (viz := self.configuration.get("LBAF_Viz")) is not None:
            # Retriveve mandatory visualization parameters
            try:
                self.grid_size = []
                for key in ("x_ranks", "y_ranks", "z_ranks"):
                    self.grid_size.append(viz[key])
                self.object_jitter = viz["object_jitter"]
                self.rank_qoi = viz["rank_qoi"]
                self.object_qoi = viz["object_qoi"]
            except Exception as e:
                self.logger.error(f"Missing LBAF-Viz configuration parameter(s): {e}")
                sys.excepthook = exc_handler
                raise SystemExit(1)

            # Verify grid size consistency
            if math.prod(self.grid_size) < self.n_ranks:
                self.logger.error(f"Grid size: {self.grid_size} < {self.n_ranks}")
                sys.excepthook = exc_handler
                raise SystemExit(1)

            # Retrieve optional parameters
            self.save_meshes = viz.get("save_meshes")
        else:
            # No visualization quantities of interest
            self.rank_qoi = self.object_qoi = self.grid_size = None

        # Parse data parameters if present
        if self.configuration.get("from_data") is not None:
            self.data_stem = self.configuration.get("from_data").get("data_stem")
            if isinstance(self.configuration.get("from_data").get("phase_ids"), str):
                range_list = list(map(int, self.configuration.get("from_data").get("phase_ids").split('-')))
                self.phase_ids = list(range(range_list[0], range_list[1] + 1))
            else:
                self.phase_ids = self.configuration.get("from_data").get("phase_ids")

        # Parse sampling parameters if present
        if self.configuration.get("from_samplers") is not None:
            self.n_objects = self.configuration.get("from_samplers").get("n_objects")
            self.n_mapped_ranks = self.configuration.get("from_samplers").get("n_mapped_ranks")
            self.communication_degree = self.configuration.get("from_samplers").get("communication_degree")
            self.load_sampler = self.configuration.get("from_samplers").get("load_sampler")
            self.volume_sampler = self.configuration.get("from_samplers").get("volume_sampler")

        # Parsing and setting up logging level
        ll = self.configuration.get("logging_level") or "info"
        logging_level = {
            "info": logging.INFO,
            "debug": logging.DEBUG,
            "error": logging.ERROR,
            "warning": logging.WARNING}
        self.logger.level = logging_level.get(ll.lower())
        self.logger.info(f"Logging level: {ll.lower()}")

        # Set output directory, local by default
        self.output_dir = os.path.abspath(self.output_dir or ".")
        self.logger.info(f"Output directory: {self.output_dir}")

    def checks_after_init(self):
        """ Checks after initialization.
        """
        # Case when phases are populated from data file
        if "data_stem" in self.__dict__:
            # Checking if log dir exists, if not, checking if dir exists in project path
            if os.path.isdir(os.path.abspath(os.path.split(self.data_stem)[0])):
                self.data_stem = os.path.abspath(self.data_stem)
            elif os.path.isdir(os.path.abspath(os.path.join(project_path, os.path.split(self.data_stem)[0]))):
                self.data_stem = os.path.abspath(os.path.join(project_path, self.data_stem))

        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)


class LBAFApp:
    def __init__(self):
        self.config_file = get_config_file()

        # Instantiate parameters
        self.params = internalParameters(config_file=self.config_file)

        # Assign logger to variable
        self.logger = self.params.logger

    def main(self):
        # Initialize random number generator
        lbstats.initialize()

        # Create list of phase instances
        phases = []
        check_schema = True if "check_schema" not in self.params.__dict__ else self.params.check_schema
        if "data_stem" in self.params.__dict__:
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
            self.logger.info(f"Starting brute force optimization")
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
                self.params.work_model.get("parameters").get(k)
                for k in ("alpha", "beta", "gamma")]
            n_a, w_min_max, a_min_max = compute_min_max_arrangements_work(
                objects, alpha, beta, gamma, self.params.n_ranks)
            if n_a != self.params.n_ranks ** len(objects):
                self.logger.error("Incorrect number of possible arrangements with repetition")
                sys.excepthook = exc_handler
                raise SystemExit(1)
            self.logger.info(f"Minimax work: {w_min_max:.4g} for {len(a_min_max)} optimal arrangements amongst {n_a}")
        else:
            self.logger.info("No brute force optimization performed")
            a_min_max = []

        # Instantiate and execute runtime
        rt = Runtime(
            phases,
            self.params.work_model,
            self.params.algorithm,
            a_min_max,
            self.logger,
            self.params.rank_qoi,
            self.params.object_qoi)
        rt.execute()

        # Instantiate phase to VT file writer if started from a log file
        if "data_stem" in self.params.__dict__:
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
            ex_writer = MeshBasedVisualizer(
                self.logger,
                qoi_request,
                phases,
                self.params.grid_size,
                self.params.object_jitter,
                self.params.output_dir,
                self.params.output_file_stem,
                rt.get_distributions(),
                rt.get_statistics())
            ex_writer.generate(
                self.params.save_meshes,
                self.params.rank_qoi)

        # Compute and print final rank load and edge volume statistics
        curr_phase = phases[-1]
        l_stats = lbstats.print_function_statistics(
            curr_phase.get_ranks(),
            lambda x: x.get_load(),
            "final rank loads",
            self.logger)
        with open(
            "imbalance.txt" if self.params.output_dir is None else os.path.join(
                self.params.output_dir, "imbalance.txt"), 'w') as imbalance_file:
            imbalance_file.write(
                f"{l_stats.imbalance}")
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
        ell = self.params.n_ranks * l_stats.average / n_o
        self.logger.info(
            f"Optimal load statistics for {n_o} objects with iso-time: {ell:.6g}")
        q, r = divmod(n_o, self.params.n_ranks)
        self.logger.info(
            f"\tminimum: {q * ell:.6g}  maximum: {(q + (1 if r else 0)) * ell:.6g}")
        self.logger.info(
            f"\tstandard deviation: {ell * math.sqrt(r * (self.params.n_ranks - r)) / self.params.n_ranks:.6g} imbalance: "
            + (f"{(self.params.n_ranks - r) / float(n_o):.6g}" if r else '0'))

        # If this point is reached everything went fine
        self.logger.info("Process completed without errors")


if __name__ == "__main__":
    LBAFApp().main()
