#@HEADER
###############################################################################
#
#                                LBAF.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
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
###############################################################################
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

from src.Model.lbsPhase import Phase
from src.Execution.lbsRuntime import Runtime
from src.IO.lbsVTDataWriter import VTDataWriter
from src.IO.lbsWriterExodusII import WriterExodusII
from src.IO.lbsStatistics import initialize, print_function_statistics, Hamming_distance
from src.Utils.logger import logger

import rank_object_enumerator as roe


class internalParameters:
    """A class to describe LBAF internal parameters
    """

    def __init__(self, config_file: str = None):
        # By default use load-only work model
        self.work_model = {"name": "LoadOnly", "parameters": {}}

        # By default use tempered criterion
        self.criterion = {"name": "Tempered", "parameters": {}}

        # Decide whether transfer must be deterministic
        self.deterministic_transfer = False

        # Number of load-balancing iterations
        self.n_iterations = 1

        # Ranks are implicitly mapped to a regular grid
        self.grid_size = [1, 1, 1]

        # Number of task objects
        self.n_objects = 1

        # Object time sampler type and parameters
        self.time_sampler_type = None
        self.time_sampler_parameters = []

        # Object communication graph time sampler type and parameters
        self.volume_sampler_type = None
        self.volume_sampler_parameters = []

        # Object communication graph degree (constant for now)
        self.communication_degree = 0

        # Object communication graph analysis enabled
        self.communication_enabled = False

        # Size of subset to which objects are initially mapped (0 = all)
        self.n_mapped_ranks = 0

        # Number of information rounds
        self.n_rounds = 1

        # Fan-out factor for information spreading
        self.fanout = 1

        # Phase-id to obtain load distribution by reading VT log files
        self.phase_id = 0

        # File name stem to obtain load distribution by reading VT log files
        self.log_file = None

        # Base name to save computed object/rank mapping for VT
        self.map_file = None

        # Decide whether Exodus output should be written
        self.exodus = False

        # Starting logger
        self.logger = logger()
        self.logging_level = "info"

        # Output directory
        self.output_dir = None

        # Output file steam
        self.output_file_stem = None

        # Generate multimedia
        self.generate_multimedia = False

        # Data files suffix (data loading)
        self.file_suffix = "vom"

        # Set default order strategy
        self.order_strategy = "arbitrary"

        # By default only one object maybe transferred at once
        self.max_objects_per_transfer = 1

        # By default False
        self.brute_force_optimization = False

        # Configuration file
        self.conf_file_found = False
        if config_file is None:
            self.conf = self.get_conf_file()
        else:
            self.conf = self.get_conf_file(conf_file=config_file)
        if self.conf_file_found:
            self.parse_conf_file()
        self.checks_after_init()

    def get_conf_file(self, conf_file=os.path.join(project_path, "src", "Applications", "conf.yaml")):
        """ Checks extension, reads YML file and returns parsed YAML file
        """

        if os.path.splitext(conf_file)[-1] in [".yml", ".yaml"] and os.path.isfile(conf_file):
            # Try to open configuration file
            self.logger.info(f"Found configuration file {conf_file}")

            try:
                with open(conf_file, "rt") as config:
                    self.conf_file_found = True
                    return yaml.safe_load(config)
            except yaml.MarkedYAMLError as err:
                self.logger.error(f"Invalid YAML file {conf_file} in line {err.problem_mark.line} ({err.problem,} "
                                  f"{err.context})")
                sys.exit(1)
        else:
            self.logger.error("Config file NOT FOUND!")
            sys.exit(1)

    def checks_after_init(self):
        """ Checks after initialization.
        """

        # Ensure that exactly one population strategy was chosen
        if (not (self.log_file or
                 (self.time_sampler_type and self.volume_sampler_type))
                or (self.log_file and
                    (self.time_sampler_type or self.volume_sampler_type))):
            self.logger.error("Exactly one strategy to populate initial phase must be chosen.")
            sys.exit(1)

        # Case when phases are populated from samplers not from log file
        if self.log_file is not None:
            # Checking if log dir exists, if not, checking if dir exists in project path
            if os.path.isdir(os.path.abspath(os.path.split(self.log_file)[0])):
                self.log_file = os.path.abspath(self.log_file)
            elif os.path.isdir(os.path.join(project_path, os.path.split(self.log_file)[0])):
                self.log_file = os.path.join(project_path, self.log_file)
            else:
                self.logger.error("LOG directory NOT FOUND!")
                sys.exit(1)

        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)

    def parse_conf_file(self):
        """ Executed when config YAML file was found and checked
        """

        # Assign parameters found in configuration file
        for param_key, param_val in self.conf.items():
            if param_key in self.__dict__:
                self.__dict__[param_key] = param_val

        # Set number of ranks in each direction for ExodusII output
        if isinstance(self.conf.get("x_procs", None), int) and self.conf.get("x_procs", 0) > 0:
            self.grid_size[0] = self.conf.get("x_procs", 0)
        if isinstance(self.conf.get("y_procs", None), int) and self.conf.get("y_procs", 0) > 0:
            self.grid_size[1] = self.conf.get("y_procs", 0)
        if isinstance(self.conf.get("z_procs", None), int) and self.conf.get("z_procs", 0) > 0:
            self.grid_size[2] = self.conf.get("z_procs", 0)

        # Set sampling parameters for random inputs
        if isinstance(self.conf.get("time_sampler_type", None), str):
            self.time_sampler_type, self.time_sampler_parameters = self.parse_sampler(self.conf["time_sampler_type"])
        if isinstance(self.conf.get("volume_sampler_type", None), str):
            self.volume_sampler_type, self.volume_sampler_parameters = self.parse_sampler(
                self.conf["volume_sampler_type"])

        # Set object ranking strategy
        if isinstance(self.conf.get("order_strategy", None), str):
            self.order_strategy = self.conf.get("order_strategy", None)

        # Set logging level
        logging_level = {
            "info": logging.INFO,
            "debug": logging.DEBUG,
            "error": logging.ERROR,
            "warning": logging.WARNING}
        self.logger.level = logging_level.get(
            self.logging_level.lower(), "info")

        # Enable communication when degree is positive
        if self.communication_degree > 0:
            self.communication_enabled = True

    def parse_sampler(self, cmd_str):
        """Parse command line arguments specifying sampler type and input parameters
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


def get_output_file_stem(params, n_ranks):
    """Build the file name for a given rank/node
    """

    # Assemble output file stem name based on phase population strategy
    if params.log_file:
        output_stem = "{}-i{}-k{}-f{}".format(
            os.path.basename(params.log_file),
            params.n_iterations,
            params.n_rounds,
            params.fanout)
    else:
        output_stem = "p{}-o{}-s{}-i{}-k{}-f{}".format(
            params.n_mapped_ranks,
            params.n_objects,
            params.time_sampler_type,
            params.n_iterations,
            params.n_rounds,
            params.fanout)

    # Return assembled stem
    return "LBAF-n{}-{}-{}-{}".format(
        n_ranks,
        output_stem,
        params.criterion["name"],
        "-".join([str(v).replace(".", "_") for v in params.criterion["parameters"].values()]))


if __name__ == "__main__":
    # Instantiate parameters
    params = internalParameters(config_file=os.path.join(project_path, "src", "Applications", "conf.yaml"))

    # Assign logger to variable
    lgr = params.logger

    # Print startup information
    sv = sys.version_info
    lgr.info(f"### Started with Python {sv.major}.{sv.minor}.{sv.micro}")

    # Keep track of total number of procs
    n_ranks = params.grid_size[0] * params.grid_size[1] * params.grid_size[2]
    if n_ranks < 2:
        lgr.info(f"Total number of ranks ({n_ranks}) must be > 1")
        sys.exit(1)

    # Initialize random number generator
    initialize()

    # Create a phase and populate it
    phase = Phase(0, logger=lgr, file_suffix=params.file_suffix)
    if params.log_file:
        # Populate phase from log files and store number of objects
        n_o = phase.populate_from_log(n_ranks, params.phase_id, params.log_file)
    else:
        # Populate phase pseudo-randomly
        phase.populate_from_samplers(
            params.n_objects,
            params.time_sampler_type,
            params.time_sampler_parameters,
            params.communication_degree,
            params.volume_sampler_type,
            params.volume_sampler_parameters,
            n_ranks,
            params.n_mapped_ranks)

        # Keep track of number of objects
        n_o = params.n_objects

    # Compute and print initial rank load and edge volume statistics
    print_function_statistics(
        phase.get_ranks(),
        lambda x: x.get_load(),
        "initial rank loads",
        logger=lgr)
    print_function_statistics(
        phase.get_edges().values(),
        lambda x: x,
        "initial sent volumes",
        logger=lgr)

    if params.brute_force_optimization:
        lgr.info(f"Starting brute force optimization")
        # Prepare input data for rank order enumerator
        objects = []
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
        alpha = params.work_model.get("parameters").get("alpha")
        beta = params.work_model.get("parameters").get("beta")
        gamma = params.work_model.get("parameters").get("gamma")
        n_a, w_min_max, a_min_max = roe.compute_min_max_arrangements_work(objects, alpha=alpha, beta=beta, gamma=gamma,
                                                                          n_ranks=n_ranks)
        if n_a != n_ranks ** len(objects):
            lgr.error("Incorrect number of possible arrangements with repetition")
            sys.exit(1)
        lgr.info(f"Minimax work: {w_min_max:.4g} for {len(a_min_max)} optimal arrangements amongst {n_a}")
    else:
        lgr.info("No brute force optimization performed")
        a_min_max = []

    # Instantiate runtime
    rt = Runtime(
        phase,
        params.work_model,
        params.criterion,
        params.order_strategy,
        a_min_max,
        lgr)
    lgr.info(f"Instantiated runtime with {params.order_strategy} object ordering strategy")

    # Execute runtime iterations when requested
    if params.n_iterations:
        rt.execute(
            params.n_iterations,
            params.n_rounds,
            params.fanout,
            params.max_objects_per_transfer,
            params.deterministic_transfer)

    # Create mapping from rank to Cartesian grid
    pgs = params.grid_size
    lgr.info(f"Mapping {n_ranks} ranks onto a {pgs[0]}x{pgs[1]}x{pgs[2]} rectilinear grid")
    grid_map = lambda x: global_id_to_cartesian(x.get_id(), params.grid_size)

    # Assemble output file name stem
    if params.output_file_stem is not None:
        output_stem = params.output_file_stem
    else:
        output_stem = get_output_file_stem(params, n_ranks)

    # Instantiate phase to VT file writer if started from a log file
    if params.log_file:
        vt_writer = VTDataWriter(
            phase,
            output_stem,
            output_dir=params.output_dir,
            logger=lgr)
        vt_writer.write()

    # If prefix parsed from command line
    if params.exodus:
        # Instantiate phase to ExodusII file writer if requested
        ex_writer = WriterExodusII(
            phase,
            grid_map,
            output_stem,
            output_dir=params.output_dir,
            logger=lgr)
        ex_writer.write(
            rt.statistics,
            rt.load_distributions,
            rt.sent_distributions,
            rt.work_distributions)

    # Create a viewer if paraview is available
    file_name = output_stem
    if params.generate_multimedia:
        from ParaviewViewerBase import ParaviewViewerBase
        if params.output_dir is not None:
            file_name = os.path.join(
                params.output_dir,
                file_name)
            output_stem = file_name
        viewer = ParaviewViewerBase.factory(
            exodus=output_stem,
            file_name=file_name,
            viewer_type="")
        reader = viewer.createViews()
        viewer.saveView(reader)

    # Create file to store imbalance statistics
    imb_file = "imbalance.txt" if params.output_dir is None else os.path.join(params.output_dir, "imbalance.txt")

    # Compute and print final rank load and edge volume statistics
    _, _, l_ave, _, _, _, _, _ = print_function_statistics(
        phase.get_ranks(),
        lambda x: x.get_load(),
        "final rank loads",
        logger=lgr,
        file=imb_file)
    print_function_statistics(
        phase.get_edges().values(),
        lambda x: x,
        "final sent volumes",
        logger=lgr)

    # Report on theoretically optimal statistics
    q, r = divmod(n_o, n_ranks)
    ell = n_ranks * l_ave / n_o
    lgr.info(f"Optimal load statistics for {n_o} objects with iso-time: {ell:.6g}")
    lgr.info(f"\tminimum: {q * ell:.6g}  maximum: {(q + (1 if r else 0)) * ell:.6g}")
    imbalance = (n_ranks - r) / float(n_o) if r else 0.
    lgr.info(f"\tstandard deviation: {ell * math.sqrt(r * (n_ranks - r)) / n_ranks:.6g}  imbalance: {imbalance:.6g}")

    # Compute Hamming distance
    # If this point is reached everything went fine
    lgr.info("Process complete ###")
