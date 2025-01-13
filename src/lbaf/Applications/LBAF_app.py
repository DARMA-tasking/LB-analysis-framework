#
#@HEADER
###############################################################################
#
#                                 LBAF_app.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
"""LBAF Application"""
import math
import os
import sys
from typing import Any, Dict, Optional, cast
import importlib
import yaml

try:
    import vttv
    USING_VTTV = True
except ModuleNotFoundError:
    USING_VTTV = False

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
import lbaf.IO.lbsStatistics as lbstats
from lbaf import PROJECT_PATH, __version__
from lbaf.Execution.lbsRuntime import Runtime
from lbaf.IO.lbsConfigurationValidator import ConfigurationValidator
from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.Model.lbsRank import Rank
from lbaf.Model.lbsObject import Object
from lbaf.Model.lbsPhase import Phase
from lbaf.Model.lbsWorkModelBase import WorkModelBase
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsJSONDataFilesValidatorLoader import \
    JSONDataFilesValidatorLoader
from lbaf.Utils.lbsLogging import Logger, get_logger
from lbaf.Utils.lbsPath import abspath
# pylint:enable=C0413:wrong-import-position

class InternalParameters:
    """Represent the parameters used internally by a LBAF Application"""
    # Private logger
    __logger: Logger

    # General input options
    check_schema: Optional[bool] = None
    output_dir: Optional[str] = None
    output_file_stem: Optional[str] = None
    file_suffix: Optional[str] = None

    # From data input options
    data_stem: Optional[str] = None
    ranks_per_node : Optional[int] = 1

    # From samplers input options
    n_ranks: Optional[int] = None
    n_objects: Optional[int] = None
    n_mapped_ranks: Optional[int] = None
    communication_degree: Optional[int] = None
    load_sampler: Optional[dict] = None
    volume_sampler: Optional[dict] = None

    # Visualization options
    rank_qoi: Optional[str] = None
    object_qoi: Optional[str] = None
    grid_size: Optional[list] = None

    # Load-balancing options
    work_model: Optional[Dict[str, dict]] = None
    algorithm: Dict[str, Any]

    def __init__(self, config: dict, base_dir: str, logger: Logger):
        self.__logger = logger

        # Initialize and check configuration
        self.validate_configuration(config)
        self.init_parameters(config, base_dir)
        self.check_parameters()

        # Print startup information
        self.__logger.info(f"Executing LBAF version {__version__}")
        svi = sys.version_info
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

        # Parse data parameters if present
        from_data = config.get("from_data")
        if from_data is not None:
            self.data_stem = from_data.get("data_stem")
            # Get data directory because data_stem includes file prefix
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
            self.expected_ranks = from_data.get("expected_ranks")
            if (rpn := from_data.get("ranks_per_node")) is not None:
                self.ranks_per_node = int(rpn)

        # Parse sampling parameters if present
        from_samplers = config.get("from_samplers")
        if from_samplers is not None:
            self.n_ranks = from_samplers.get("n_ranks")
            self.n_objects = from_samplers.get("n_objects", {})
            self.n_mapped_ranks = from_samplers.get("n_mapped_ranks")
            self.communication_degree = from_samplers.get("communication_degree")
            self.load_sampler = from_samplers.get("load_sampler")
            self.volume_sampler = from_samplers.get("volume_sampler")

        # Parse visualizer parameters when available
        if (viz := config.get("visualization")) is not None:

            # Ensure that vttv module was found
            if not USING_VTTV:
                raise ModuleNotFoundError("Visualization enabled but vt-tv module not found.")

            # Retrieve mandatory visualization parameters
            try:
                self.grid_size = []
                for key in ("x_ranks", "y_ranks", "z_ranks"):
                    self.grid_size.append(viz[key])
                self.object_jitter = viz["object_jitter"]
                self.rank_qoi = viz["rank_qoi"]
                self.object_qoi = viz.get("object_qoi")
            except Exception as e:
                self.__logger.error(
                    f"Missing visualization configuration parameter(s): {e}")
                raise SystemExit(1) from e

            # Retrieve optional parameters
            self.save_meshes = viz.get("save_meshes", False)
            self.continuous_object_qoi = viz.get("force_continuous_object_qoi", False)

        # Set output directory, local by default
        self.output_dir = abspath(config.get("output_dir", '.'), relative_to=base_dir)

        # Parse JSON writer parameters when available
        self.json_params = {}
        if (wrt_json := config.get("write_JSON")) is not None:
            # Retrieve mandatory writer parameters
            try:
                self.json_params["compressed"] = wrt_json["compressed"]
            except Exception as e:
                self.__logger.error(
                    f"Missing JSON writer configuration parameter(s): {e}")
                raise SystemExit(1) from e

            # Retrieve optional parameters
            for k_out, k_wrt, v_def in [
                    ("json_output_suffix", "suffix", "json"),
                    ("communications", "communications", False),
                    ("offline_lb_compatible", "offline_lb_compatible", False),
                    ("lb_iterations", "lb_iterations", False)]:
                self.json_params[k_out] = wrt_json.get(k_wrt, v_def)

    def check_parameters(self):
        """Checks after initialization."""

        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.isdir(self.output_dir):
                os.makedirs(self.output_dir)


class LBAFApplication:
    """LBAF application class."""

    def __init__(self):
        self.__parameters: Optional[InternalParameters] = None
        self.__json_writer: Optional[VTDataWriter] = None
        self.__args: Optional[dict] = None
        self.__logger = get_logger()

    def __parse_args(self):
        """Parse arguments."""
        parser = PromptArgumentParser(
            allow_abbrev=False,
            description="Run a Load-Balancing Simulation with some configuration",
            prompt_default=False)
        parser.add_argument(
            "-c", "--configuration",
            help=("Path to the config file. If path is relative it must be resolvable from "
                  "either the current working directory or the config directory"),
            default="conf.yaml")
        parser.add_argument(
            "-v", "--verbose",
            help="Verbosity level. If 1, print all possible rank QOI. If 2, print all possible rank and object QOI.",
            default="0")
        self.__args = parser.parse_args()

    def __read_configuration_file(self, path: str):
        if os.path.splitext(path)[-1] in [".yml", ".yaml"]:
            # Try to open configuration file in read+text mode
            try:
                with open(path, "rt", encoding="utf-8") as file_io:
                    data = yaml.safe_load(file_io)
                    if not data.get("overwrite_validator", True):
                        self.__logger.info(
                            f"Option 'overwrite_validator' in configuration file: {path} is set to False")
            except yaml.MarkedYAMLError as err:
                err_line = err.problem_mark.line if err.problem_mark is not None else -1
                self.__logger.error(
                    f"Invalid YAML file {path} in line {err_line} ({err.problem}) {err.context}")
                raise SystemExit(1) from err
        else:
            raise SystemExit(1)
        return data

    def __merge(self, src: dict, dest: dict) -> dict:
        """Merges dictionaries. Internally used to merge configuration data"""
        data = dest.copy()
        for k in src:
            if not k in data:
                # if new key
                data[k] = src[k]
            else:
                # if key exists in both src and dest
                if isinstance(src[k], dict) and isinstance(data[k], dict):
                    data[k] = self.__merge(src[k], dest[k])
                else:
                    data[k] = src[k]
        return data

    def __merge_configurations(self, *config_path):
        """Generates a unique configuration dict from multiple configurations from a path list"""
        config = {}
        for path in config_path:
            next_config = self.__read_configuration_file(path)
            config = self.__merge(next_config, config)
        return config

    def __configure(self, *config_path):
        """Configure the application using the configuration file(s) at the given path(s).

        :param config_path: The configuration file path.
            If multiple then provide it from the most generic to the most specialized.
        :returns: The configuration as a dictionary
        """

        # merge configurations
        config = self.__merge_configurations(*config_path)

        # Change logger (with parameters from the configuration)
        lvl = cast(str, config.get("logging_level", "info"))
        config_dir = os.path.dirname(config_path[-1]) # Directory of the most specialized configuration
        log_to_file = config.get("log_to_file", None)
        self.__logger = get_logger(
            name="lbaf",
            level=lvl,
            log_to_console=config.get("log_to_console", None) is None,
            log_to_file=None if log_to_file is None else abspath(
                config.get("log_to_file"), relative_to=config_dir)
        )
        self.__logger.info(f"Logging level: {lvl.lower()}")
        if log_to_file is not None:
            log_to_file_path = abspath(
                config.get("log_to_file"), relative_to=config_dir)
            self.__logger.info(f"Logging to file: {log_to_file_path}")

        # Instantiate the application internal parameters
        self.__parameters = InternalParameters(
            config=config, base_dir=config_dir, logger=self.__logger)

        # Create VT writer except when explicitly turned off
        self.__json_writer = VTDataWriter(
            self.__logger,
            self.__parameters.output_dir,
            self.__parameters.output_file_stem,
            self.__parameters.json_params) if self.__parameters.json_params else None

        return config

    def __resolve_config_path(self, config_path) -> str:
        """Find the config file from the '-configuration' command line argument and returns its absolute path
        (if configuration file path is relative it is searched in the current working directory and at the end in the
        {PROJECT_PATH}/config directory)

        :raises FileNotFoundError: if configuration file cannot be found
        """
        # Search config file in the current working directory if relative
        path = config_path
        path_list = []
        path_list.append(path)
        if (
            path is not None and
            not os.path.isfile(path) and
            not os.path.isabs(config_path) and PROJECT_PATH is not None
        ):
            # Then search config file relative to the config folder
            search_dir = abspath("config", relative_to=PROJECT_PATH)
            path = search_dir + '/' + config_path
            path_list.append(path)

        # Verify path correctness
        if not os.path.isfile(path):
            raise FileNotFoundError(
                "Configuration file not found. If a relative path was provided the file may not exist "
                "in current working directory or in the `<project_path>/config` directory")
        self.__logger.info(f"Found configuration file at path {path}")
        return path

    def __print_statistics(self, phase: Phase, phase_name: str, work_model: WorkModelBase = None):
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
        shared_memory_stats = lbstats.print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_shared_memory(),
            f"{phase_name} rank shared memory",
            self.__logger)
        lbstats.print_function_statistics(
            phase.get_ranks(),
            lambda x: x.get_max_memory_usage(),
            f"{phase_name} maximum memory usage",
            self.__logger)
        if shared_memory_stats.get_maximum():
            lbstats.print_function_statistics(
                phase.get_ranks(),
                lambda x: x.get_homed_blocks_ratio(),
                f"{phase_name} homed_blocks_ratio",
                self.__logger)
            lbstats.print_function_statistics(
                phase.get_ranks(),
                lambda x: x.get_number_of_uprooted_blocks(),
                f"{phase_name} number_of_uprooted_blocks",
                self.__logger)

        # Print edge statistics
        lbstats.print_function_statistics(
            phase.get_edge_maxima().values(),
            lambda x: x,
            f"{phase_name} sent volumes",
            self.__logger)

        if work_model is not None:
            w_stats = lbstats.print_function_statistics(
                phase.get_ranks(),
                work_model.compute,
                f"{phase_name} rank work",
                self.__logger)
        else:
            w_stats = None

        # Return rank load and work statistics
        return l_stats, w_stats

    def __print_qoi(self) -> int:
        """Print list of implemented QOI based on the '-verbosity' command line argument."""
        verbosity = int(self.__args.verbose)

        r = Rank(self.__logger)
        rank_qois = r.get_qois()
        o = Object(seq_id=0)
        object_qois = o.get_qois()

        # Print QOI based on verbosity level
        if verbosity > 0:
            self.__logger.info("List of Implemented QOI:")
        if verbosity == 1:
            self.__logger.info("\tRank QOI:")
            for name, _ in rank_qois.items():
                self.__logger.info("\t\t" + name)
        elif verbosity > 1:
            self.__logger.info("\tRank QOI:")
            for name, _ in rank_qois.items():
                self.__logger.info("\t\t" + name)
            self.__logger.info("")
            self.__logger.info("\tObject QOI:")
            for name, _ in object_qois.items():
                self.__logger.info("\t\t" + name)

    def run(self, cfg=None, cfg_dir=None):
        """Run the LBAF application."""
        # If no configuration was passed directly, look for the file(s)
        if cfg is None:
            # Parse command line arguments
            self.__parse_args()

            # Print list of implemented QOI (according to verbosity argument)
            self.__print_qoi()

            # Warn if default configuration is used because not set as argument
            if self.__args.configuration is None:
                self.__logger.warning("No configuration file given. Fallback to default `conf.yaml` file in "
                                    "working directory or in the project config directory !")
                self.__args.configuration = "conf.yaml"

            # Find configuration files
            config_file_list = []

            # Global configuration (optional)
            try:
                config_file_list.append(self.__resolve_config_path("global.yaml"))
            except FileNotFoundError:
                pass

            # Local/Specialized configuration (required)
            try:
                config_file_list.append(self.__resolve_config_path(self.__args.configuration))
            except(FileNotFoundError) as err:
                self.__logger.error(err)
                raise SystemExit(-1) from err

            # Apply configuration
            cfg = self.__configure(*config_file_list)

        else:
            self.__parameters = InternalParameters(
                config=cfg, base_dir=cfg_dir, logger=self.__logger)

        # Download of JSON data files validator required to continue
        loader = JSONDataFilesValidatorLoader()
        if loader.run(cfg.get("overwrite_validator", True)) != 0:
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
        # Create dictionary for phase instances
        phases = {}

        # Check schema
        check_schema = True if "check_schema" not in self.__parameters.__dict__ else self.__parameters.check_schema

        # Initialize variables
        reader, n_ranks = None, None

        # Populate phase depending on chosen mechanism
        if self.__parameters.data_stem:
            # Populate phase from log files and store number of objects
            file_suffix = None if "file_suffix" not in self.__parameters.__dict__ else self.__parameters.file_suffix

            # Initializing reader
            reader = LoadReader(
                file_prefix=self.__parameters.data_stem,
                logger=self.__logger,
                file_suffix=file_suffix if file_suffix is not None else "json",
                check_schema=check_schema,
                expected_ranks=self.__parameters.expected_ranks,
                ranks_per_node=self.__parameters.ranks_per_node)

            # Retrieve n_ranks
            n_ranks = reader.n_ranks

            # Iterate over phase IDs
            for phase_id in self.__parameters.phase_ids:
                # Create a phase and populate it
                phase = Phase(
                    self.__logger, phase_id, reader=reader)
                phase.populate_from_log(phase_id)
                phases[phase_id] = phase
        else:
            n_ranks = self.__parameters.n_ranks
            phase_id = 0
            phase = Phase(self.__logger, phase_id)
            phase.populate_from_samplers(
                n_ranks,
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
        if ("brute_force_optimization" in self.__parameters.__dict__
                and self.__parameters.algorithm["name"] != "BruteForce"):
            self.__logger.info("Starting brute force optimization")
            objects = initial_phase.get_objects()
            alpha, beta, gamma = [
                self.__parameters.work_model.get("parameters", {}).get(k)
                for k in ("alpha", "beta", "gamma")]
            _n_a, _w_min_max, a_min_max = lbstats.compute_min_max_arrangements_work(
                objects, alpha, beta, gamma, n_ranks, logger=self.__logger)
        else:
            a_min_max = []

        # Instantiate runtime
        runtime = Runtime(
            phases,
            self.__parameters.work_model,
            self.__parameters.algorithm,
            a_min_max,
            self.__logger)

        # Execute runtime for specified phases
        offline_lb_compatible = self.__parameters.json_params.get(
            "offline_lb_compatible", False)
        rebalanced_phase = runtime.execute(
            self.__parameters.algorithm.get("phase_id", 0),
            1 if offline_lb_compatible else 0,
            self.__parameters.json_params.get("lb_iterations", False))

        # Instantiate phase to VT file writer when requested
        if self.__json_writer:
            if offline_lb_compatible:
                # Add rebalanced phase when present
                if not rebalanced_phase:
                    self.__logger.warning(
                        "No rebalancing took place for offline load-balancing")
                else:
                    # Determine if a phase with same index was present
                    if _existing_phase := phases.get(p_id := rebalanced_phase.get_id()):
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

                # Write all phasesOA
                self.__logger.info(
                    f"Writing all ({len(phases)}) phases for offline load-balancing")
                self.__json_writer.write(phases)
            else:
                # Add new phase when load balancing when offline mode not selected
                self.__logger.info(f"Creating rebalanced phase {phase_id}")
                self.__json_writer.write({phase_id: rebalanced_phase})

        # Generate meshes and multimedia when requested
        if self.__parameters.grid_size:
            # Verify grid size consistency
            if math.prod(self.__parameters.grid_size) < n_ranks:
                self.__logger.error(
                    "Grid size: {self.__parameters.grid_size} < {n_ranks}")
                raise SystemExit(1)

            # Call vt-tv visualization when requested
            if USING_VTTV:
                self.__logger.info("Calling vt-tv")

                # Serialize data to JSON-formatted string
                rank_phases = {}
                for p in phases.values():
                    for r in p.get_ranks():
                        rank_phases.setdefault(r.get_id(), {})
                        rank_phases[r.get_id()][p.get_id()] = r
                ranks_json_str = []
                for i in range(len(rank_phases.items())):
                    ranks_json_str.append(self.__json_writer._json_serializer((i, rank_phases[i])))

                # Retrieve vt-tv parameters
                vttv_params = {
                    "x_ranks": self.__parameters.grid_size[0],
                    "y_ranks": self.__parameters.grid_size[1],
                    "z_ranks": self.__parameters.grid_size[2],
                    "object_jitter": self.__parameters.object_jitter,
                    "rank_qoi": self.__parameters.rank_qoi,
                    "object_qoi": self.__parameters.object_qoi,
                    "save_meshes": self.__parameters.save_meshes,
                    "force_continuous_object_qoi": self.__parameters.continuous_object_qoi,
                    "output_visualization_dir": self.__parameters.output_dir,
                    "output_visualization_file_stem": self.__parameters.output_file_stem}

                # Retrieve grid topology
                num_ranks = (
                    self.__parameters.grid_size[0] *
                    self.__parameters.grid_size[1] *
                    self.__parameters.grid_size[2] )

                vttv.tvFromJson(ranks_json_str, str(vttv_params), num_ranks)

        # Report on rebalanced phase when available
        if rebalanced_phase:
            l_stats, w_stats = self.__print_statistics(
                rebalanced_phase, "rebalanced", runtime.get_work_model())
            with open(
                "imbalance.txt" if self.__parameters.output_dir is None
                else os.path.join(
                    self.__parameters.output_dir,
                    "imbalance.txt"), 'w', encoding="utf-8") as imbalance_file:
                imbalance_file.write(f"{l_stats.get_imbalance()}")

            with open(
                "w_max.txt" if self.__parameters.output_dir is None
                else os.path.join(
                    self.__parameters.output_dir,
                    "w_max.txt"), 'w', encoding="utf-8") as w_max_file:
                w_max_file.write(f"{w_stats.get_maximum()}")

        for r in initial_phase.get_ranks():
            if node := r.get_node() is not None:
                print(r, id(r), node.get_max_memory_usage(initial_phase))

        if rebalanced_phase:
            print()
            for r in rebalanced_phase.get_ranks():
                if node := r.get_node() is not None:
                    print(r, id(r), node.get_max_memory_usage(rebalanced_phase))

        # If this point is reached everything went fine
        self.__logger.info("Process completed without errors")
        return 0


if __name__ == "__main__":
    LBAFApplication().run()
