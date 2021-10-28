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
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    exit(1)

import getopt
import math

import bcolors
import yaml
try:
    import paraview.simple
except:
    pass

from src.Model.lbsPhase import Phase
from src.Execution.lbsRuntime import Runtime
from src.IO.lbsLoadWriterVT import LoadWriterVT
from src.IO.lbsWriterExodusII import WriterExodusII
from src.IO.lbsStatistics import initialize, print_function_statistics


class ggParameters:
    """A class to describe LBAF parameters
    """

    def __init__(self):
        # By default use modified Grapevine criterion
        self.criterion = 1

        # By default use modified Grapevine PMF
        self.pmf_type = 0

        # Number of load-balancing iterations
        self.n_iterations = 1

        # Processors are implicitly mapped to a regular grid
        self.grid_size = [1, 1, 1]

        # Number of task objects
        self.n_objects = 1

        # Object time sampler type and parameters
        self.time_sampler_type = None
        self.time_sampler_parameters = []

        # Object communication graph time sampler type and parameters
        self.weight_sampler_type = None
        self.weight_sampler_parameters = []

        # Object communication graph degree (constant for now)
        self.communication_degree = 0

        # Object communication graph analysis enabled
        self.communication_enabled = False

        # Size of subset to which objects are initially mapped (0 = all)
        self.n_processors = 0

        # Number of gossiping rounds
        self.n_rounds = 1

        # Fan-out factor for information spreading (gossiping)
        self.fanout = 1

        # Relative overload threshold for load transfer
        self.threshold = 1.

        # Phase-id to obtain load distribution by reading VT log files
        self.phase_id = 0

        # File name stem to obtain load distribution by reading VT log files
        self.log_file = None

        # Base name to save computed object/processor mapping for VT
        self.map_file = None

        # Decide whether actual destination loads should be computed
        self.actual_dst_load = False

        # Decide whether Exodus output should be written
        self.exodus = False

        # Do not be verbose by default
        self.verbose = False

        # Output directory
        self.output_dir = None

        # Generate multimedia
        self.generate_multimedia = False

        # Data files suffix (data loading)
        self.file_suffix = "vom"

        # Configuration file
        self.conf_file_found = False
        self.conf = self.get_conf_file()
        if self.conf_file_found:
            self.parse_conf_file()
        else:
            self.parse_command_line()
        self.checks_after_init()

    def usage(self):
        """Provide online help
        """

        print("Usage:")
        print("\t [-c <tc>]   transfer criterion:")
        print("\t\t\t 0: Grapevine original")
        print("\t\t\t 1: Grapevine modified (default)")
        print("\t\t\t 2: strict localizer")
        print("\t\t\t 3: relaxed localizer")
        print("\t [-n <nf>]   normalization factor for transfer PMF:")
        print("\t\t\t 0: load average or maximum sender load (default)")
        print("\t\t\t 1: recipient load (NS variant)")
        print("\t [-i <ni>]   number of load-balancing iterations")
        print("\t [-x <npx>]  number of procs in x direction")
        print("\t [-y <npy>]  number of procs in y direction")
        print("\t [-z <npz>]  number of procs in z direction")
        print("\t [-o <no>]   number of objects")
        print("\t [-p <np>]   number of initially used processors")
        print("\t [-k <nr>]   number of gossiping rounds")
        print("\t [-f <fo>]   gossiping fan-out value")
        print("\t [-r <rt>]   overload relative threshold")
        print("\t [-t <ts>]   object times sampler: "
              "<ts> in {uniform,lognormal}")
        print("\t [-w <ws>]   communications weights sampler: "
              "<cs> in {uniform,lognormal}")
        print("\t [-s <ts>]   time stepping for reading VT load logs")
        print("\t [-l <blog>] base file name for reading VT load logs")
        print("\t [-m <bmap>] base file name for VT object/proc mapping")
        print("\t [-d <d>]    object communication degree "
              "(no communication if 0) ")
        print("\t [-b <odir>] output directory")
        print("\t [-j <fsuf>] file suffix for data files(reading data)")
        print("\t [-v]        make standard output more verbose")
        print("\t [-a]        use actual destination loads")
        print("\t [-e]        generate Exodus type visualization output")
        print("\t [-g]        generate multimedia")
        print("\t [-h]        help: print this message and exit")
        print('')

    def parse_command_line(self):
        """Parse command line and fill grid gossiper parameters
        """

        # Try to hash command line with respect to allowable flags
        try:
            opts, args = getopt.getopt(
                sys.argv[1:],
                "ab:c:d:ef:ghi:j:k:l:m:n:o:p:r:s:t:vw:x:y:z:")
        except getopt.GetoptError:
            print(bcolors.ERR
                + "** ERROR: incorrect command line arguments."
                + bcolors.END)
            self.usage()
            sys.exit(1)

        # Parse arguments and assign corresponding member variable values
        for o, a in opts:
            try:
                i = int(a)
            except:
                i = None

            if o == '-h':
                self.usage()
                sys.exit(0)
            elif o == '-c':
                self.criterion = i
            elif o == '-n':
                self.pmf_type = i
            elif o == '-i':
                if i > -1:
                    self.n_iterations = i
            elif o == '-x':
                if i > 0:
                    self.grid_size[0] = i
            elif o == '-y':
                if i > 0:
                    self.grid_size[1] = i
            elif o == '-z':
                if i > 0:
                    self.grid_size[2] = i
            elif o == '-o':
                if i > 0:
                    self.n_objects = i
            elif o == '-p':
                if i > 0:
                    self.n_processors = i
            elif o == "-k":
                if i > 0:
                    self.n_rounds = i
            elif o == '-f':
                if i > 0:
                    self.fanout = i
            elif o == '-r':
                x = float(a)
                if x > 1.:
                    self.threshold = x
            elif o == '-t':
                (self.time_sampler_type,
                self.time_sampler_parameters) = parse_sampler(a)
            elif o == '-w':
                (self.weight_sampler_type,
                self.weight_sampler_parameters) = parse_sampler(a)
            elif o == '-s':
                 if i > -1:
                     self.phase_id = i
            elif o == '-l':
                self.log_file = a
            elif o == '-m':
                self.map_file = a
            elif o == '-d':
                if i > 0:
                    self.communication_degree = i
                    self.communication_enabled = True
            elif o == '-a':
                self.actual_dst_load = True
            elif o == '-e':
                self.exodus = True
            elif o == '-v':
                self.verbose = True
            elif o == '-g':
                self.generate_multimedia = True
            elif o == '-b':
                self.output_dir = a
            elif o == '-j':
                self.file_suffix = a

    def get_conf_file(self, conf_file=os.path.join(project_path, 'src', 'Applications', 'conf.yaml')):
        """ Checks extension, reads YML file and returns parsed YAML file
        """
        if os.path.splitext(conf_file)[-1] in ['.yml', '.yaml'] and os.path.isfile(conf_file):
            print(f"{bcolors.OKMSG}Config file {conf_file} FOUND!{bcolors.END}")
            try:
                with open(conf_file, 'rt') as config:
                    self.conf_file_found = True
                    return yaml.safe_load(config)
            except yaml.MarkedYAMLError as err:
                print(f"{bcolors.ERR}ERROR: Invalid YAML file {conf_file} in line {err.problem_mark.line} "
                      f"({err.problem,} {err.context}){bcolors.END}")
                sys.exit(1)
        else:
            print(f"{bcolors.ERR}Config file NOT FOUND!{bcolors.END}")

    def checks_after_init(self):
        """ Checks after initialization.
        """
        # Ensure that exactly one population strategy was chosen
        if (not (self.log_file or
                 (self.time_sampler_type and self.weight_sampler_type))
                or (self.log_file and
                    (self.time_sampler_type or self.weight_sampler_type))):
            print(bcolors.ERR
                  + "** ERROR: exactly one strategy to populate initial phase "
                    "must be chosen."
                  + bcolors.END)
            self.usage()
            sys.exit(1)

        # Checking if log dir exists, if not, checking if dir exists in project path
        if os.path.isdir(os.path.abspath(os.path.split(self.log_file)[0])):
            self.log_file = os.path.abspath(self.log_file)
        elif os.path.isdir(os.path.join(project_path, os.path.split(self.log_file)[0])):
            self.log_file = os.path.join(project_path, self.log_file)
        else:
            print(f"{bcolors.ERR}LOG directory NOT FOUND!{bcolors.END}")
            sys.exit(1)

        # Checking if output dir exists, if not, creating one
        if self.output_dir is not None:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)

    def parse_conf_file(self):
        """ Executed when config YAML file was found and checked
        """
        for param_key, param_val in self.conf.items():
            if self.__dict__.get(param_key, 'SomeRidiculousValue') != 'SomeRidiculousValue':
                self.__dict__[param_key] = param_val
        if isinstance(self.conf.get('x_procs', None), int) and self.conf.get('x_procs', 0) > 0:
            self.grid_size[0] = self.conf.get('x_procs', 0)
        if isinstance(self.conf.get('y_procs', None), int) and self.conf.get('y_procs', 0) > 0:
            self.grid_size[1] = self.conf.get('y_procs', 0)
        if isinstance(self.conf.get('z_procs', None), int) and self.conf.get('z_procs', 0) > 0:
            self.grid_size[2] = self.conf.get('z_procs', 0)
        if isinstance(self.conf.get('time_sampler_type', None), str):
            self.time_sampler_type, self.time_sampler_parameters = parse_sampler(self.conf['time_sampler_type'])
        if isinstance(self.conf.get('weight_sampler_type', None), str):
            self.weight_sampler_type, self.weight_sampler_parameters = parse_sampler(self.conf['weight_sampler_type'])
        if self.communication_degree > 0:
            self.communication_enabled = True


def parse_sampler(cmd_str):
    """Parse command line arguments specifying sampler type and input parameters
       Example: lognormal,1.0,10.0
    """

    # Default return values
    sampler_type = None
    sampler_args = []

    # Try to parse the sampler from `cmd_str`
    a_s = cmd_str.split(',')
    if len(a_s):
        sampler_type = a_s[0].lower()
        for p in a_s[1:]:
            try:
                x = float(p)
            except:
                print(bcolors.ERR
                    + "** ERROR: `{}` cannot be converted to a float".format(p)
                    + bcolors.END)
                sys.exit(1)
            sampler_args.append(x)

    # Error check the sampler parsed from input string
    if sampler_type not in (
            "uniform",
            "lognormal"):
        print(bcolors.ERR
            + "** ERROR: unsupported sampler type: {}".format(
            sampler_type)
            + bcolors.END)
        sys.exit(1)
    if len(sampler_args) != 2:
        print(bcolors.ERR
            + ("** ERROR: expected two parameters for sampler type: {},"
               " got {}").format(
            sampler_type,
            len(sampler_args))
            + bcolors.END)
        sys.exit(1)

    # Return the sampler parsed from the input argument
    return sampler_type, sampler_args


def global_id_to_cartesian(id, grid_sizes):
    """Map global index to its Cartesian coordinates in a grid
    """

    # Sanity check
    n01 = grid_sizes[0] * grid_sizes[1]
    if id < 0  or id >= n01 * grid_sizes[2]:
        return None

    # Compute successive euclidean divisions
    k, r = divmod(id, n01)
    j, i = divmod(r, grid_sizes[0])

    # Return Cartesian coordinates
    return i, j, k


def get_output_file_stem(params):
    """Build the file name for a given rank/node
    """

    # Assemble output file stem name based on phase population strategy
    if params.log_file:
        output_stem = "l{}-i{}-k{}-f{}".format(
            os.path.basename(params.log_file),
            params.n_iterations,
            params.n_rounds,
            params.fanout)
    else:
        output_stem = "p{}-o{}-s{}-i{}-k{}-f{}".format(
            params.n_processors,
            params.n_objects,
            params.time_sampler_type,
            params.n_iterations,
            params.n_rounds,
            params.fanout)

    # Return assembled stem
    return "LBAF-n{}-{}-t{}".format(
        n_p,
        output_stem,
        "{}".format(params.threshold).replace('.', '_'))


if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print(bcolors.HEADER
        + "[LBAF] "
        + bcolors.END
        + "### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print(bcolors.HEADER
        + "[LBAF] "
        + bcolors.END
        + "Parsing command line arguments")
    params = ggParameters()

    # Keep track of total number of procs
    n_p = params.grid_size[0] * params.grid_size[1] * params.grid_size[2]
    if n_p < 2:
        print(bcolors.ERR
            + "** ERROR: Total number of processors ({}) must be > 1".format(n_p)
            + bcolors.END)
        sys.exit(1)

    # Initialize random number generator
    initialize()

    # Create a phase and populate it
    phase = Phase(0, params.verbose, file_suffix=params.file_suffix)
    if params.log_file:
        # Populate phase from log files and store number of objects
        n_o = phase.populate_from_log(n_p,
                                      params.phase_id,
                                      params.log_file)


    else:
        # Populate phase pseudo-randomly
        phase.populate_from_samplers(params.n_objects,
                                     params.time_sampler_type,
                                     params.time_sampler_parameters,
                                     params.communication_degree,
                                     params.weight_sampler_type,
                                     params.weight_sampler_parameters,
                                     n_p,
                                     params.n_processors)

        # Keep track of number of objects
        n_o = params.n_objects

    # Compute and print initial processor load and link weight statistics
    print_function_statistics(
        phase.get_processors(),
        lambda x: x.get_load(),
        "initial processor loads",
        params.verbose)
    print_function_statistics(
        phase.get_edges().values(),
        lambda x: x,
        "initial link weights",
        params.verbose)

    # Instantiate runtime
    rt = Runtime(phase,
                            params.criterion,
                            params.actual_dst_load,
                            params.verbose)
    rt.execute(params.n_iterations,
               params.n_rounds,
               params.fanout,
               params.threshold,
               params.pmf_type)

    # Create mapping from processor to Cartesian grid
    print(bcolors.HEADER
        + "[LBAF] "
        + bcolors.END
        + "Mapping {} processors onto a {}x{}x{} rectilinear grid".format(
        n_p,
        *params.grid_size))
    grid_map = lambda x: global_id_to_cartesian(x.get_id(), params.grid_size)

    # Assemble output file name stem
    output_stem = get_output_file_stem(params)

    # Instantiate phase to VT file writer if started from a log file
    if params.log_file:
        vt_writer = LoadWriterVT(phase, f"{output_stem}", output_dir=params.output_dir)
        vt_writer.write()

    # If prefix parsed from command line
    if params.exodus:
        # Instantiate phase to ExodusII file writer if requested
        ex_writer = WriterExodusII(phase, grid_map, f"{output_stem}", output_dir=params.output_dir)
        ex_writer.write(rt.statistics,
                        rt.load_distributions,
                        rt.sent_distributions,
                        params.verbose)

    # Create a viewer if paraview is available
    file_name = output_stem

    if params.generate_multimedia:
        from ParaviewViewerBase import ParaviewViewerBase
        if params.output_dir is not None:
            file_name = os.path.join(params.output_dir, file_name)
            output_stem = file_name
        viewer = ParaviewViewerBase.factory(exodus=output_stem, file_name=file_name, viewer_type='')
        reader = viewer.createViews()
        viewer.saveView(reader)

    # Compute and print final processor load and link weight statistics
    _, _, l_ave, _, _, _, _, _ = print_function_statistics(
        phase.get_processors(),
        lambda x: x.get_load(),
        "final processor loads",
        params.verbose)
    print_function_statistics(
        phase.get_edges().values(),
        lambda x: x,
        "final link weights",
        params.verbose)

    # Report on theoretically optimal statistics
    q, r = divmod(n_o, n_p)
    ell = n_p * l_ave / n_o
    print(bcolors.HEADER
        + "[LBAF] "
        + bcolors.END
        + "Optimal load statistics for {} objects "
          "with iso-time: {:.6g}".format(
        n_o,
        ell))
    print("\tminimum: {:.6g}  maximum: {:.6g}".format(
        q * ell,
        (q + (1 if r else 0)) * ell))
    imbalance = (n_p - r) / float(n_o) if r else 0.
    imb_file = 'imbalance.txt' if params.output_dir is None else os.path.join(params.output_dir, 'imbalance.txt')
    with open(imb_file, 'w') as file:
        file.write(f"{imbalance}")
    print("\tstandard deviation: {:.6g}  imbalance: {:.6g}".format(
        ell * math.sqrt(r * (n_p - r)) / n_p, imbalance))

    # If this point is reached everything went fine
    print(bcolors.HEADER
        + "[LBAF] "
        + bcolors.END
        + " Process complete ###")
