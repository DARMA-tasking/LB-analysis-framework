""" LBAF application module
"""
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
    print(f'Can not add project path to system path! Exiting!\nERROR: {path_ex}')
    raise SystemExit(1) from path_ex
try:
    import paraview.simple #pylint: disable=E0401,W0611
except: #pylint: disable=W0718,W0702
    pass

# pylint: disable=C0413
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.colors import green
# pylint: enable=C0413

def get_config_file() -> str:
    """ Parses command line argument and returns config file path.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the config file.", default='conf.yaml')
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
    """ Makes sure that SchemaValidator can be imported, and it's the latest version available.
    """
    module_name = green(f"[{os.path.splitext(os.path.split(__file__)[-1])[0]}]")

    def save_schema_validator_and_init_file(import_dir: str):
        with open(os.path.join(import_dir, '__init__.py'), 'wt', encoding='utf-8') as init_file:
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
            raise ConnectionError('Probably there is no internet connection') from err

    overwrite_validator = True
    config_file = None
    if __name__ == '__main__':
        config_file = get_config_file()
        with open(config_file, 'rt', encoding='utf-8') as config:
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
        print(f'{module_name} Option \'overwrite_validator\' in configuration file: {config_file} is set to False\n'
              f'{module_name} In case of `ModuleNotFoundError: No module named \'lbaf.imported\'` set it to True.')


check_and_get_schema_validator()

# pylint: disable=C0413
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
# pylint: enable=C0413

class InternalParameters:
    """Represent LBAF application parameters
    """
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
    # from_samplers options
    n_objects: int
    n_mapped_ranks: int
    communication_degree: int
    load_sampler: dict
    volume_sampler: dict

    def __init__(self, config_file: str):
        config = self.load_config(from_file=config_file)

        # init lbaf logger
        lvl = cast(str, config.get('logging_level', 'info'))
        self.logger = logger(
            name='lbaf',
            level=lvl,
            theme=config.get('terminal_background', None),
            log_to_console=config.get('log_to_file', None) is None,
            log_to_file=config.get('log_to_file', None)
        )
        self.logger.info('Logging level: %s', lvl.lower())

        self.validate_configuration(config)
        self.init_parameters(config, config_file)
        self.check_parameters()

        # Print startup information
        self.logger.info('Executing LBAF version %s', __version__)
        svi = sys.version_info
        self.logger.info('Executing with Python %s.%s.%s', svi.major, svi.minor, svi.micro)

    def load_config(self, from_file: str)-> dict:
        """ Check extension, read YML file and return parsed YAML configuration file
        """
        if os.path.splitext(from_file)[-1] in [".yml", ".yaml"] and os.path.isfile(from_file):
            # Try to open configuration file
            logger().info('Found configuration file %s', from_file)
            try:
                with open(from_file, 'rt', encoding='utf-8') as config:
                    self.configuration_file_found = True
                    return yaml.safe_load(config)
            except yaml.MarkedYAMLError as err:
                logger().error(
                    'Invalid YAML file %s in line %s (%s) %s',
                    from_file, err.problem_mark.line if err.problem_mark is not None else -1, err.problem, err.context
                )
                sys.excepthook = exc_handler
                raise SystemExit(1) from err
        else:
            logger().error('Configuration file in %s not found', from_file)
            sys.excepthook = exc_handler
            raise SystemExit(1)

    def validate_configuration(self, config: dict):
        """ Configuration file validation. """
        ConfigurationValidator(config_to_validate=config, logger=self.logger).main()

    def init_parameters(self, config: dict, config_file: str):
        """ Execute when YAML configuration file was found and checked
        """
        # Get top-level allowed configuration keys
        self.__allowed_config_keys = cast(list, ConfigurationValidator.allowed_keys())

        # Assign parameters found in configuration file
        for param_key, param_val in config.items():
            if param_key in self.__allowed_config_keys:
                self.__dict__[param_key] = param_val

        # Parse LBAF_Viz parameters when available
        if (viz := config.get("LBAF_Viz")) is not None:
            # Retriveve mandatory visualization parameters
            try:
                self.grid_size = []
                for key in ("x_ranks", "y_ranks", "z_ranks"):
                    self.grid_size.append(viz[key])
                self.object_jitter = viz["object_jitter"]
                self.rank_qoi = viz["rank_qoi"]
                self.object_qoi = viz["object_qoi"]
            except Exception as ex:
                self.logger.error('Missing LBAF-Viz configuration parameter(s): %s', ex)
                sys.excepthook = exc_handler
                raise SystemExit(1) from ex

            # Verify grid size consistency
            if math.prod(self.grid_size) < self.n_ranks:
                self.logger.error('Grid size: %s < %s', self.grid_size, self.n_ranks)
                sys.excepthook = exc_handler
                raise SystemExit(1)

            # Retrieve optional parameters
            self.save_meshes = viz.get("save_meshes")
        else:
            # No visualization quantities of interest
            self.rank_qoi = self.object_qoi = self.grid_size = None

        config_file_dir = os.path.dirname(config_file)

        # Parse data parameters if present
        if config.get("from_data") is not None:
            self.data_stem = config.get("from_data").get("data_stem")
            # get path if relative to the configuration file
            if not os.path.isabs(self.data_stem):
                self.data_stem = os.path.abspath(config_file_dir + '/' + self.data_stem)

            if isinstance(config.get("from_data", {}).get("phase_ids"), str):
                range_list = list(map(int, config.get("from_data").get("phase_ids").split('-')))
                self.phase_ids = list(range(range_list[0], range_list[1] + 1))
            else:
                self.phase_ids = config.get("from_data").get("phase_ids", {})

        # Parse sampling parameters if present
        if config.get("from_samplers") is not None:
            self.n_objects = config.get("from_samplers").get("n_objects", {})
            self.n_mapped_ranks = config.get("from_samplers").get("n_mapped_ranks")
            self.communication_degree = config.get("from_samplers").get("communication_degree")
            self.load_sampler = config.get("from_samplers").get("load_sampler")
            self.volume_sampler = config.get("from_samplers").get("volume_sampler")

        # Set output directory, local by default
        self.output_dir = config.get('output_dir', '.')
        # get path if relative to the configuration file
        if not os.path.isabs(self.output_dir):
            self.output_dir = os.path.abspath(config_file_dir + '/' + self.output_dir)
        self.logger.info('Output directory: %s', self.output_dir)

    def check_parameters(self):
        """ Checks after initialization.
        """
        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)

class LBAFApp:
    """LBAF application class"""
    def __init__(self):
        self.config_file = get_config_file()

        # Instantiate parameters
        self.params = InternalParameters(config_file=self.config_file)

        # Assign logger to variable
        self.logger = self.params.logger

    def main(self):
        """LBAFApp entrypoint to run"""
        # Initialize random number generator
        lbstats.initialize()

        # Create list of phase instances
        phases = [] #type: List[Phase]
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
        if "brute_force_optimization" in self.params.__dict__ and self.params.algorithm['name'] != 'BruteForce':
            # Prepare input data for rank order enumerator
            self.logger.info('Starting brute force optimization')
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
                'Minimax work: %s for %s optimal arrangements amongst %s',
                f'{w_min_max:4g}', len(a_min_max), n_a
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
                self.params.output_dir, "imbalance.txt"), 'w', encoding='utf-8') as imbalance_file:
            imbalance_file.write(
                f"{l_stats.imbalance}") #pylint: disable=E1101
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
        ell = self.params.n_ranks * l_stats.average / n_o #pylint: disable=E1101
        self.logger.info('Optimal load statistics for %s objects with iso-time: %s', n_o, f'{ell:6g}')
        q, r = divmod(n_o, self.params.n_ranks) #pylint: disable=C0103
        self.logger.info(
            '\tminimum: %s  maximum: %s',
            f'{q * ell:6g}',
            f'{q + (1 if r else 0) * ell:6g}'
        )
        self.logger.info(
            '\tstandard deviation: %s imbalance: %s',
            f'{ell * math.sqrt(r * (self.params.n_ranks - r)) / self.params.n_ranks:6g}',
            f'{(self.params.n_ranks - r) / float(n_o):6g}' if r else '0'
        )

        # If this point is reached everything went fine
        self.logger.info('Process completed without errors')


if __name__ == "__main__":
    LBAFApp().main()
