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

from lbaf.Model.lbsPhase import Phase
from lbaf.Execution.lbsRuntime import Runtime
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.IO.lbsWriterExodusII import WriterExodusII
from lbaf.IO.lbsStatistics import initialize, print_function_statistics
from lbaf.Utils.logger import logger

from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work


class internalParameters:
    """A class to describe LBAF internal parameters
    """

    def __init__(self, config_file: str):
        # Starting logger
        self.logger = logger()

        # Print startup information
        sv = sys.version_info
        self.logger.info(f"Executing with Python {sv.major}.{sv.minor}.{sv.micro}")

        self.__allowed_config_keys = [
            "algorithm",
            "brute_force_optimization",
            "communication_degree",
            "exodus",
            "file_suffix",
            "generate_multimedia",
            "data_stem",
            "logging_level",
            "output_dir",
            "output_file_stem",
            "n_mapped_ranks",
            "n_objects",
            "phase_id",
            "terminal_background",
            "time_sampler",
            "volume_sampler",
            "work_model",
            "x_procs",
            "y_procs",
            "z_procs"]

        # Initializing instance variables
        self.algorithm = None
        self.brute_force_optimization = None
        self.communication_degree = None
        self.exodus = None
        self.file_suffix = None
        self.generate_multimedia = None
        self.grid_size = None
        self.data_stem = None
        self.logging_level = None
        self.output_dir = None
        self.output_file_stem = None
        self.n_mapped_ranks = None
        self.n_objects = None
        self.phase_id = None
        self.terminal_background = None
        self.time_sampler = None
        self.time_sampler_type = None
        self.time_sampler_parameters = None
        self.volume_sampler = None
        self.volume_sampler_type = None
        self.volume_sampler_parameters = None
        self.work_model = None
        self.x_procs = None
        self.y_procs = None
        self.z_procs = None

        # Read configuration values from file
        self.configuration_file_found = False
        self.configuration = self.get_configuration_file(conf_file=config_file)
        if self.configuration_file_found:
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

    def checks_after_init(self):
        """ Checks after initialization.
        """
        # Ensure that an algorithm was chosen
        if not (algo := self.algorithm) or not algo.get("name") or not algo.get("parameters"):
            self.logger.error("An algorithm name and its parameters must be defined")
            sys.exit(1)

        # Ensure that a work model algorithm was chosen
        if not (wm := self.work_model) or not wm.get("name"):
            self.logger.error("A work model name must be defined")
            sys.exit(1)

        # Ensure that exactly one population strategy was chosen
        # Make sure that when populate from sampling both time_sampler and volume_sampler are defined
        # Both data and sampling are set
        both_on = self.data_stem is not None and bool(self.time_sampler is not None or self.volume_sampler is not None)
        # Both data and sampling are not set
        both_off = self.data_stem is None and bool(self.time_sampler is None or self.volume_sampler is None)

        if both_on or both_off:
            self.logger.error("Exactly one strategy to populate phase must be chosen: either log file or sampler types")
            sys.exit(1)

        # Case when phases are populated from data file
        if self.data_stem is not None:
            # Checking if log dir exists, if not, checking if dir exists in project path
            if os.path.isdir(os.path.abspath(os.path.split(self.data_stem)[0])):
                self.data_stem = os.path.abspath(self.data_stem)
            elif os.path.isdir(os.path.abspath(os.path.join(project_path, os.path.split(self.data_stem)[0]))):
                self.data_stem = os.path.abspath(os.path.join(project_path, self.data_stem))

        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)

    def parse_conf_file(self):
        """ Execute when YAML configuration file was found and checked
        """
        # Assign parameters found in configuration file
        for param_key, param_val in self.configuration.items():
            if param_key in self.__allowed_config_keys:
                self.__dict__[param_key] = param_val

        self.generate_multimedia = None if not self.generate_multimedia else self.generate_multimedia
        self.brute_force_optimization = None if not self.brute_force_optimization else self.brute_force_optimization

        # Set number of ranks in each direction for ExodusII output
        self.grid_size = []
        for i, key in enumerate(["x_procs", "y_procs", "z_procs"]):
            n_procs = self.configuration.get(key)
            # Reject invalid values
            if not isinstance(n_procs, int) or n_procs < 1:
                self.logger.error(f"Invalid number of processors in {key[0]}-direction for ExodusII output: {n_procs}")
                sys.exit(1)
            self.grid_size.append(n_procs)

        # Set sampling parameters for random inputs
        if isinstance(self.configuration.get("time_sampler_type", None), str):
            self.time_sampler_type, self.time_sampler_parameters = self.parse_sampler(
                self.configuration["time_sampler_type"])
        if isinstance(self.configuration.get("volume_sampler_type", None), str):
            self.volume_sampler_type, self.volume_sampler_parameters = self.parse_sampler(
                self.configuration["volume_sampler_type"])

        # Set logging level
        ll = self.logging_level or "info"
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

    def parse_sampler(self, cmd_str):
        """ Parse command line arguments specifying sampler type and input parameters
            Example: lognormal,1.0,10.0
        """

        # Default return values
        sampler_type = None
        sampler_args = []

        # Try to parse the sampler from `cmd_str`
        a_s = cmd_str.split(",")
        if len(a_s):
            sampler_type = a_s[0].lower()
            for p in a_s[1:]:
                try:
                    x = float(p)
                except:
                    self.logger.error(f"{p} cannot be converted to a float")
                    sys.exit(1)
                sampler_args.append(x)

        # Error check the sampler parsed from input string
        if sampler_type not in ("uniform", "lognormal"):
            self.logger.error(f"Unsupported sampler type: {sampler_type}")
            sys.exit(1)
        if len(sampler_args) != 2:
            self.logger.error(f"Expected two parameters for sampler type: {sampler_type}, got {len(sampler_args)}")
            sys.exit(1)

        # Return the sampler parsed from the input argument
        return sampler_type, sampler_args


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
        if self.params.file_suffix is not None:
            phase = Phase(0, self.logger, self.params.file_suffix)
        else:
            phase = Phase(0, self.logger)
        if self.params.data_stem:
            # Try to populate phase from log files and store number of objects
            if not isinstance(self.params.phase_id, int) or self.params.phase_id < 0:
                self.logger.error(f"A valid phase ID is required to populate from VT log file: {self.params.phase_id}")
                sys.exit(1)
            self.params.n_objects = phase.populate_from_log(n_ranks, self.params.phase_id, self.params.data_stem)
        else:
            # Try to populate phase pseudo-randomly
            if self.params.n_objects is None or not isinstance(self.params.n_objects, int) or self.params.n_objects < 1:
                self.logger.error(f"A valid number of objects is required: {self.params.n_objects}")
                sys.exit(1)
            if self.params.communication_degree is None or not isinstance(self.params.communication_degree, int) \
                    or self.params.communication_degree < 0:
                self.logger.error(f"A valid communication degree is required: {self.params.communication_degree}")
                sys.exit(1)
            if self.params.time_sampler is None or self.params.time_sampler.get("name") is None \
                    or self.params.time_sampler.get("parameters") is None:
                self.logger.error("A time sampler name and its parameters must be defined")
                sys.exit(1)
            if self.params.volume_sampler is None or self.params.volume_sampler.get("name") is None \
                    or self.params.volume_sampler.get("parameters") is None:
                self.logger.error("A volume sampler name and its parameters must be defined")
                sys.exit(1)
            self.params.n_mapped_ranks = 0 if self.params.n_mapped_ranks is None else self.params.n_mapped_ranks
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
        if self.params.brute_force_optimization is not None and self.params.algorithm["name"] != "BruteForce":
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
        if self.params.data_stem:
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
        if self.params.generate_multimedia is not None:
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
