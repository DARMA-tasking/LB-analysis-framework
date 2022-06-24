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
    raise SystemExit(1)
try:
    import paraview.simple
except:
    pass

from lbaf import __version__
from lbaf.Applications.rank_object_enumerator import compute_min_max_arrangements_work
from lbaf.Execution.lbsRuntime import Runtime
from lbaf.IO.configurationValidator import ConfigurationValidator
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
        self.logger = logger()

        # Print startup information
        self.logger.info(f"Executing LBAF version {__version__}")
        sv = sys.version_info
        self.logger.info(f"Executing with Python {sv.major}.{sv.minor}.{sv.micro}")

        self.__allowed_config_keys = (
            "algorithm",
            "brute_force_optimization",
            "generate_meshes",
            "file_suffix",
            "from_data",
            "from_samplers",
            "generate_multimedia",
            "logging_level",
            "n_ranks",
            "output_dir",
            "output_file_stem",
            "terminal_background",
            "show_traceback",
            "work_model"
        )

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
                raise SystemExit(1)
        else:
            self.logger.error(f"Configuration file in {conf_file} not found")
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

        # Parse whether meshes must be generated
        if (gm := self.configuration.get("generate_meshes")) is not None:
            self.grid_size = []
            for key in ("x_ranks", "y_ranks", "z_ranks"):
                self.grid_size.append(gm.get(key))
            if math.prod(self.grid_size) < self.n_ranks:
                self.logger.error(f"Grid size: {self.grid_size} < {self.n_ranks}")
                raise SystemExit(1)
            self.object_jitter = gm.get("object_jitter")

        # Parse data parameters if present
        if self.configuration.get("from_data") is not None:
            self.data_stem = self.configuration.get("from_data").get("data_stem")
            self.phase_ids = self.configuration.get("from_data").get("phase_ids")

        # Parse sampling parameters if present
        if self.configuration.get("from_samplers") is not None:
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
        self.config_file = self.__get_config_file()

        # Instantiate parameters
        self.params = internalParameters(config_file=self.config_file)

        # Assign logger to variable
        self.logger = self.params.logger

        # Traceback setup
        if "show_traceback" in self.params.__dict__:
            if self.params.show_traceback:
                self.logger.info(f"Showing Traceback")
            else:
                self.logger.info(f"Hiding Traceback")

                def exception_handler(exception_type, exception, traceback):
                    """ Exception handler for hiding traceback. """
                    self.logger.error(f"{exception_type.__name__} {exception}")

                sys.excepthook = exception_handler
        else:
            self.logger.info(f"Hiding Traceback")
            def exception_handler(exception_type, exception, traceback):
                """ Exception handler for hiding traceback. """
                self.logger.error(f"{exception_type.__name__} {exception}")

            sys.excepthook = exception_handler

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
        # Initialize random number generator
        lbstats.initialize()

        # Create list of phase instances
        phases = []
        if "data_stem" in self.params.__dict__:
            # Populate phase from log files and store number of objects
            for phase_id in self.params.phase_ids:
                # Create a phase and populate it
                if (suffix := self.params.__dict__.get("file_suffix")):
                    phase = Phase(self.logger, phase_id, suffix)
                else:
                    phase = Phase(self.logger, phase_id)
                phase.populate_from_log(
                    self.params.n_ranks,
                    phase_id,
                    self.params.data_stem)
                phases.append(phase)
        else:
            # Populate phase pseudo-randomly a phase 0
            phase = Phase(self.logger, 0)
            phase.populate_from_samplers(
                self.params.n_ranks,
                self.params.n_objects,
                self.params.time_sampler,
                self.params.volume_sampler,
                self.params.communication_degree,
                self.params.n_mapped_ranks)
            phases.append(phase)

        # Compute and print initial rank load and edge volume statistics
        phase_0 = phases[0]
        lbstats.print_function_statistics(
            phase_0.get_ranks(),
            lambda x: x.get_load(),
            "initial rank loads",
            self.logger)
        lbstats.print_function_statistics(
            phase_0.get_edges().values(),
            lambda x: x,
            "initial sent volumes",
            self.logger)

        # Perform brute force optimization when needed
        if "brute_force_optimization" in self.params.__dict__ and self.params.algorithm["name"] != "BruteForce":
            # Prepare input data for rank order enumerator
            self.logger.info(f"Starting brute force optimization")
            objects = []

            # Iterate over ranks
            for rank in phase_0.get_ranks():
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
                objects, alpha, beta, gamma, self.params.n_ranks)
            if n_a != self.params.n_ranks ** len(objects):
                self.logger.error("Incorrect number of possible arrangements with repetition")
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
            self.logger)
        rt.execute()

        # Instantiate phase to VT file writer if started from a log file
        if "data_stem" in self.params.__dict__:
            vt_writer = VTDataWriter(
                phase_0,
                self.logger,
                self.params.output_file_stem,
                output_dir=self.params.output_dir)
            vt_writer.write()

        # Generate meshes and multimedia when requested
        gen_meshes = self.params.__dict__.get("generate_meshes")
        gen_mulmed = self.params.__dict__.get("generate_multimedia")
        if gen_meshes or gen_mulmed:
            # Instantiate mesh based visualizer and execute as requested
            ex_writer = MeshBasedVisualizer(
                self.logger,
                phases,
                self.params.grid_size,
                self.params.object_jitter,
                self.params.output_dir,
                self.params.output_file_stem,
                rt.distributions,
                rt.statistics)
            ex_writer.generate(gen_meshes, gen_mulmed)

        # Compute and print final rank load and edge volume statistics
        _, _, l_ave, _, _, _, _, _ = lbstats.print_function_statistics(
            phase_0.get_ranks(),
            lambda x: x.get_load(),
            "final rank loads",
            self.logger,
            file_name=("imbalance.txt"
                       if self.params.output_dir is None
                       else os.path.join(self.params.output_dir, "imbalance.txt")))
        lbstats.print_function_statistics(
            phase_0.get_edges().values(),
            lambda x: x,
            "final sent volumes",
            self.logger)

        # Report on theoretically optimal statistics
        n_o = phase_0.get_number_of_objects()
        q, r = divmod(n_o, self.params.n_ranks)
        ell = self.params.n_ranks * l_ave / n_o
        self.logger.info(f"Optimal load statistics for {n_o} objects with iso-time: {ell:.6g}")
        self.logger.info(f"\tminimum: {q * ell:.6g}  maximum: {(q + (1 if r else 0)) * ell:.6g}")
        imbalance = (self.params.n_ranks - r) / float(n_o) if r else 0.
        self.logger.info(
            f"\tstandard deviation: {ell * math.sqrt(r * (self.params.n_ranks - r)) / self.params.n_ranks:.6g} "
            f"imbalance: {imbalance:.6g}")

        # If this point is reached everything went fine
        self.logger.info("Process completed without errors")


if __name__ == "__main__":
    LBAFApp().main()
