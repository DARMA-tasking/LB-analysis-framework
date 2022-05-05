import argparse
import os
import sys
import logging
import math
import yaml

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    sys.exit(1)
try:
    import paraview.simple
except:
    pass

from lbaf import __version__
from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work
from lbaf.Execution.lbsRuntime import Runtime
from lbaf.IO.configurationValidator import ConfigurationValidator
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.IO.lbsWriterExodusII import WriterExodusII
from lbaf.IO.lbsStatistics import initialize, print_function_statistics
from lbaf.Model.lbsPhase import Phase
from lbaf.Utils.logger import logger


class internalParameters:
    """A class to describe LBAF internal parameters
    """

    def __init__(self, config_file: str):
        # Starting logger
        self.logger = logger()

        # Print startup information
        self.logger.info(f"Executing LBAF version {__version__}")
        sv = sys.version_info
        self.logger.info(f"Executing with Python {sv.major}.{sv.minor}.{sv.micro}")

        self.__allowed_config_keys = [
            "algorithm",
            "brute_force_optimization",
            "exodus",
            "file_suffix",
            "from_data",
            "from_samplers",
            "generate_multimedia",
            "logging_level",
            "output_dir",
            "output_file_stem",
            "terminal_background",
            "work_model"
        ]

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
                sys.exit(1)
        else:
            self.logger.error(f"Configuration file in {conf_file} not found")
            sys.exit(1)

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

        # Parsing exodus if present
        if self.configuration.get('exodus') is not None:
            self.grid_size = []
            for key in ["x_procs", "y_procs", "z_procs"]:
                self.grid_size.append(self.configuration.get("exodus").get(key))

        # Parsing from data parameters if present
        if self.configuration.get('from_data') is not None:
            self.data_stem = self.configuration.get("from_data").get("data_stem")
            self.phase_id = self.configuration.get("from_data").get("phase_id")

        # Parsing sampling parameters if present
        if self.configuration.get('from_samplers') is not None:
            self.n_objects = self.configuration.get("from_samplers").get("n_objects")
            self.n_mapped_ranks = self.configuration.get("from_samplers").get("n_mapped_ranks")
            self.communication_degree = self.configuration.get("from_samplers").get("communication_degree")
            self.time_sampler = self.configuration.get("from_samplers").get("time_sampler")
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
        self.output_dir = os.path.abspath(self.output_dir or '.')
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


def global_id_to_cartesian(id, grid_sizes):
    """Map global index to its Cartesian coordinates in a grid
    """

    # Sanity check
    n01 = grid_sizes[0] * grid_sizes[1]
    if id < 0 or id >= n01 * grid_sizes[2]:
        return None

    # Compute successive euclidean divisions
    k, r = divmod(id, n01)
    j, i = divmod(r, grid_sizes[0])

    # Return Cartesian coordinates
    return i, j, k


class LBAFApp:
    def __init__(self):
        self.config_file = self.__get_config_file()

        # Instantiate parameters
        self.params = internalParameters(config_file=self.config_file)

        # Assign logger to variable
        self.logger = self.params.logger

    @staticmethod
    def __get_config_file() -> str:
        """ Parses command line argument and returns config file path. """
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", help="Path to the config file.")
        args = parser.parse_args()
        if args.config:
            config_file = os.path.abspath(args.config)
        else:
            config_file = os.path.join(project_path, "lbaf", "Applications", "conf.yaml")

        return config_file

    def main(self):
        # Keep track of total number of procs
        n_ranks = self.params.grid_size[0] * self.params.grid_size[1] * self.params.grid_size[2]
        if n_ranks < 2:
            self.logger.info(f"Total number of ranks ({n_ranks}) must be > 1")
            sys.exit(1)

        # Initialize random number generator
        initialize()

        # Create a phase and populate it
        if "file_suffix" in self.params.__dict__:
            phase = Phase(0, self.logger, self.params.file_suffix)
        else:
            phase = Phase(0, self.logger)
        if "data_stem" in self.params.__dict__:
            # Try to populate phase from log files and store number of objects
            self.params.n_objects = phase.populate_from_log(n_ranks, self.params.phase_id, self.params.data_stem)
        else:
            # Try to populate phase pseudo-randomly
            phase.populate_from_samplers(n_ranks, self.params.n_objects, self.params.time_sampler,
                                         self.params.volume_sampler, self.params.communication_degree,
                                         self.params.n_mapped_ranks)

        # Compute and print initial rank load and edge volume statistics
        print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_load(),
            "initial rank loads",
            logger=self.logger)
        print_function_statistics(
            phase.get_edges().values(),
            lambda x: x,
            "initial sent volumes",
            logger=self.logger)

        # Perform brute force optimization when needed
        if "brute_force_optimization" in self.params.__dict__ and self.params.algorithm["name"] != "BruteForce":
            # Prepare input data for rank order enumerator
            self.logger.info(f"Starting brute force optimization")
            objects = []

            # Iterate over ranks
            for rank in phase.get_ranks():
                for o in rank.get_objects():
                    entry = {
                        "id": o.get_id(),
                        "time": o.get_time(),
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
            alpha = self.params.work_model.get("parameters").get("alpha")
            beta = self.params.work_model.get("parameters").get("beta")
            gamma = self.params.work_model.get("parameters").get("gamma")
            n_a, w_min_max, a_min_max = compute_min_max_arrangements_work(
                objects, alpha, beta, gamma, n_ranks)
            if n_a != n_ranks ** len(objects):
                self.logger.error("Incorrect number of possible arrangements with repetition")
                sys.exit(1)
            self.logger.info(f"Minimax work: {w_min_max:.4g} for {len(a_min_max)} optimal arrangements amongst {n_a}")
        else:
            self.logger.info("No brute force optimization performed")
            a_min_max = []

        # Instantiate and execute runtime
        rt = Runtime(
            phase,
            self.params.work_model,
            self.params.algorithm,
            a_min_max,
            self.logger)
        rt.execute()

        # Create mapping from rank to Cartesian grid
        pgs = self.params.grid_size
        self.logger.info(f"Mapping {n_ranks} ranks onto a {pgs[0]}x{pgs[1]}x{pgs[2]} rectilinear grid")
        grid_map = lambda x: global_id_to_cartesian(x.get_id(), self.params.grid_size)

        # Try to output file name stem
        if self.params.output_file_stem is None:
            self.logger.error("An output file stem must be provided")
            sys.exit(1)

        # Instantiate phase to VT file writer if started from a log file
        if "data_stem" in self.params.__dict__:
            vt_writer = VTDataWriter(
                phase,
                self.params.output_file_stem,
                output_dir=self.params.output_dir,
                logger=self.logger)
            vt_writer.write()

        # If prefix parsed from command line
        if self.params.exodus:
            # Instantiate phase to ExodusII file writer if requested
            ex_writer = WriterExodusII(
                phase,
                grid_map,
                self.params.output_file_stem,
                output_dir=self.params.output_dir,
                logger=self.logger)
            ex_writer.write(rt.distributions, rt.statistics)

        # Create a viewer if paraview is available
        file_name = self.params.output_file_stem
        if self.params.__dict__.get("generate_multimedia") is not None \
                and self.params.__dict__.get("generate_multimedia"):
            from ParaviewViewerBase import ParaviewViewerBase
            if self.params.output_dir is not None:
                file_name = os.path.join(self.params.output_dir, file_name)
                output_file_stem = file_name
                viewer = ParaviewViewerBase.factory(
                    exodus=output_file_stem,
                    file_name=file_name,
                    viewer_type='')
                reader = viewer.createViews()
            viewer.saveView(reader)

        # Create file to store imbalance statistics
        imb_file = "imbalance.txt" if self.params.output_dir is None else os.path.join(self.params.output_dir,
                                                                                       "imbalance.txt")

        # Compute and print final rank load and edge volume statistics
        _, _, l_ave, _, _, _, _, _ = print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_load(),
            "final rank loads",
            logger=self.logger,
            file=imb_file)
        print_function_statistics(
            phase.get_edges().values(),
            lambda x: x,
            "final sent volumes",
            logger=self.logger)

        # Report on theoretically optimal statistics
        q, r = divmod(self.params.n_objects, n_ranks)
        ell = n_ranks * l_ave / self.params.n_objects
        self.logger.info(f"Optimal load statistics for {self.params.n_objects} objects with iso-time: {ell:.6g}")
        self.logger.info(f"\tminimum: {q * ell:.6g}  maximum: {(q + (1 if r else 0)) * ell:.6g}")
        imbalance = (n_ranks - r) / float(self.params.n_objects) if r else 0.
        self.logger.info(
            f"\tstandard deviation: {ell * math.sqrt(r * (n_ranks - r)) / n_ranks:.6g}  imbalance: {imbalance:.6g}")

        # If this point is reached everything went fine
        self.logger.info("Process completed without errors")


if __name__ == "__main__":
    LBAFApp().main()
