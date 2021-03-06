#@HEADER
###############################################################################
#
#                                NodeGossiper.py
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
NodeGossiper_module_aliases = {}
for m in [
    "bcolors",
    "getopt",
    "math",
    "os",
    "subprocess",
    "sys",
   ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in NodeGossiper_module_aliases:
            globals()[NodeGossiper_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("** ERROR: failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

if __name__ == '__main__':
    if __package__ is None:
        sys.path.append(
            os.path.dirname(
            os.path.dirname(
            os.path.abspath(__file__))))
        from Model                  import lbsPhase
        from Execution              import lbsRuntime
        from IO                     import lbsLoadWriterVT, lbsWriterExodusII, lbsStatistics
        try:
            from ParaviewViewerBase import ParaviewViewerBase
            globals()["has_paraview"] = True
        except:
            globals()["has_paraview"] = False
    else:
        from ..Model                  import lbsPhase
        from ..Execution              import lbsRuntime
        from ..IO                     import lbsLoadWriterVT, lbsWriterExodusII, lbsStatistics
        try:
            from ..ParaviewViewerBase import ParaviewViewerBase
            globals()["has_paraview"] = True
        except:
            globals()["has_paraview"] = False

###############################################################################
class ggParameters:
    """A class to describe NodeGossiper parameters
    """

    ###########################################################################
    def __init__(self):
        # By default use modified Grapevine criterion
        self.criterion = 1

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

        # Time-step to obtain load distribution by reading VT log files
        self.time_step = 0

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

    ###########################################################################
    def usage(self):
        """Provide online help
        """

        print("Usage:")
        print("\t [-c <tc>]   transfer criterion:")
        print("\t\t\t 0: Grapevine original")
        print("\t\t\t 1: Grapevine modified (default)")
        print("\t\t\t 2: strict localizer")
        print("\t\t\t 3: relaxed localizer")
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
        print("\t [-v]        make standard output more verbose")
        print("\t [-a]        use actual destination loads")
        print("\t [-e]        generate Exodus type visualization output")
        print("\t [-h]        help: print this message and exit")
        print('')

    ###########################################################################
    def parse_command_line(self):
        """Parse command line and fill grid gossiper parameters
        """

        # Try to hash command line with respect to allowable flags
        try:
            opts, args = getopt.getopt(
                sys.argv[1:],
                "ac:i:x:y:z:o:p:k:f:r:t:w:s:l:m:d:veh")
        except getopt.GetoptError:
            print(bcolors.ERR
                + "** ERROR: incorrect command line arguments."
                + bcolors.END)
            self.usage()
            return True

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
                     self.time_step = i
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
            return True

	# No line parsing error occurred
        return False

###############################################################################
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

###############################################################################
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

###############################################################################
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
    return "NodeGossiper-n{}-{}-t{}".format(
        n_p,
        output_stem,
        "{}".format(params.threshold).replace('.', '_'))

###############################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print(bcolors.HEADER
        + "[NodeGossiper] "
        + bcolors.END
        + "### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print(bcolors.HEADER
        + "[NodeGossiper] "
        + bcolors.END
        + "Parsing command line arguments")
    params = ggParameters()
    if params.parse_command_line():
       sys.exit(1)

    # Keep track of total number of procs
    n_p = params.grid_size[0] * params.grid_size[1] * params.grid_size[2]
    if n_p < 2:
        print(bcolors.ERR
            + "** ERROR: Total number of processors ({}) must be > 1".format(n_p)
            + bcolors.END)
        sys.exit(1)

    # Initialize random number generator
    lbsStatistics.initialize()

    # Create a phase and populate it
    phase = lbsPhase.Phase(0, params.verbose)
    if params.log_file:
        # Populate phase from log files and store number of objects
        n_o = phase.populate_from_log(n_p,
                                      params.time_step,
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
    lbsStatistics.print_function_statistics(
        phase.get_processors(),
        lambda x: x.get_load(),
        "initial processor loads",
        params.verbose)
    lbsStatistics.print_function_statistics(
        phase.get_edges().values(),
        lambda x: x,
        "initial link weights",
        params.verbose)

    # Instantiate runtime
    rt = lbsRuntime.Runtime(phase,
                            params.criterion,
                            params.actual_dst_load,
                            params.verbose)
    rt.execute(params.n_iterations,
               params.n_rounds,
               params.fanout,
               params.threshold)

    # Create mapping from processor to Cartesian grid
    print(bcolors.HEADER
        + "[NodeGossiper] "
        + bcolors.END
        + "Mapping {} processors onto a {}x{}x{} rectilinear grid".format(
        n_p,
        *params.grid_size))
    grid_map = lambda x: global_id_to_cartesian(x.get_id(), params.grid_size)

    # Assemble output file name stem
    output_stem = get_output_file_stem(params)

    # Instantiate phase to VT file writer if started from a log file
    if params.log_file:
        vt_writer = lbsLoadWriterVT.LoadWriterVT(
            phase,
            "{}".format(output_stem))
        vt_writer.write(params.time_step)

    # If prefix parsed from command line
    if params.exodus:
        # Instantiate phase to ExodusII file writer if requested
        ex_writer = lbsWriterExodusII.WriterExodusII(
            phase,
            grid_map,
            "{}".format(output_stem))
        ex_writer.write(rt.statistics,
                        rt.load_distributions,
                        rt.sent_distributions,
                        params.verbose)

    # Create a viewer if paraview is available
    if globals().get("has_paraview"):
        viewer = ParaviewViewerBase.factory(
            output_stem,
            params.exodus,
            "")
        reader = viewer.createViews()
        viewer.saveView(reader)

    # Compute and print final processor load and link weight statistics
    _, _, l_ave, _, _, _, _, _ = lbsStatistics.print_function_statistics(
        phase.get_processors(),
        lambda x: x.get_load(),
        "final processor loads",
        params.verbose)
    lbsStatistics.print_function_statistics(
        phase.get_edges().values(),
        lambda x: x,
        "final link weights",
        params.verbose)

    # Report on theoretically optimal statistics
    q, r = divmod(n_o, n_p)
    ell = n_p * l_ave / n_o
    print(bcolors.HEADER
        + "[NodeGossiper] "
        + bcolors.END
        + "Optimal load statistics for {} objects "
          "with iso-time: {:.6g}".format(
        n_o,
        ell))
    print("\tminimum: {:.6g}  maximum: {:.6g}".format(
        q * ell,
        (q + (1 if r else 0)) * ell))
    print("\tstandard deviation: {:.6g}  imbalance: {:.6g}".format(
        ell * math.sqrt(r * (n_p - r)) / n_p,
        (n_p - r) / float(n_o) if r else 0.))

    # If this point is reached everything went fine
    print(bcolors.HEADER
        + "[NodeGossiper] "
        + bcolors.END
        + " Process complete ###")

###############################################################################
