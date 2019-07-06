#!/usr/bin/env python2.7
########################################################################
NodeGossiper_module_aliases = {}
for m in [
    "os",
    "subprocess",
    "getopt",
    "math",
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
        print("*  WARNING: Failed to import " + m + ". {}.".format(e))
        globals()[has_flag] = False

if __name__ == '__main__':
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from Model     import lbsEpoch
        from Execution import lbsRuntime
        from IO        import lbsLoadWriterVT, lbsLoadWriterExodusII, lbsStatistics
    else:
        from ..Model     import lbsEpoch
        from ..Execution import lbsRuntime
        from ..IO        import lbsLoadWriterVT, lbsLoadWriterExodusII, lbsStatistics

########################################################################
class ggParameters:
    """A class to describe NodeGossiper parameters
    """

    ####################################################################
    def __init__(self):
        # Do not be verbose by default
        self.verbose = False

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

    ####################################################################
    def usage(self):
        """Provide online help
        """

        print("Usage:")
        print("\t [-i <ni>]   number of load-balancing iterations")
        print("\t [-x <npx>]  number of procs in x direction")
        print("\t [-y <npy>]  number of procs in y direction")
        print("\t [-z <npz>]  number of procs in z direction")
        print("\t [-o <no>]   number of objects")
        print("\t [-p <np>]   number of initially used processors")
        print("\t [-k <nr>]   number of gossiping rounds")
        print("\t [-f <fo>]   gossiping fan-out value")
        print("\t [-r <rt>]   overload relative threshold")
        print("\t [-t <ts>]   object times sampler: <ts> in {uniform,lognormal}")
        print("\t [-w <ws>]   communications weights sampler: <cs> in {uniform,lognormal}")
        print("\t [-s <ts>]   time stepping for reading VT load logs")
        print("\t [-l <blog>] base file name for reading VT load logs")
        print("\t [-m <bmap>] base file name for VT object/proc mapping")
        print("\t [-d <d>]    object communication degree  (no communication if 0) ")
        print("\t [-v]        make standard output more verbose")
        print("\t [-h]        help: print this message and exit")
        print('')

    ####################################################################
    def parse_command_line(self):
        """Parse command line and fill grid gossiper parameters
        """

        # Try to hash command line with respect to allowable flags
        try:
            opts, args = getopt.getopt(sys.argv[1:], "f:hk:i:o:p:r:s:t:vx:y:z:l:m:d:w:")
        except getopt.GetoptError:
            print("** ERROR: incorrect command line arguments.")
            self.usage()
            return True

        # Parse arguments and assign corresponding member variable values
        for o, a in opts:
            try:
                i = int(a)
            except:
                i = None
            if o == "-h":
                self.usage()
                sys.exit(0)
            elif o == "-v":
                self.verbose = True
            elif o == "-i":
                if i > -1:
                    self.n_iterations = i
            elif o == "-s":
                if i > -1:
                    self.time_step = i
            elif o == "-x":
                if i > 0:
                    self.grid_size[0] = i
            elif o == "-y":
                if i > 0:
                    self.grid_size[1] = i
            elif o == "-z":
                if i > 0:
                    self.grid_size[2] = i
            elif o == "-o":
                if i > 0:
                    self.n_objects = i
            elif o == "-p":
                if i > 0:
                    self.n_processors = i
            elif o == "-d":
                if i > 0:
                    self.communication_degree = i
                    self.communication_enabled = True
            elif o == "-t":
                self.time_sampler_type, self.time_sampler_parameters = parse_sampler(a)
            elif o == "-w":
                self.weight_sampler_type, self.weight_sampler_parameters = parse_sampler(a)
            elif o == "-k":
                if i > 0:
                    self.n_rounds = i
            elif o == "-f":
                if i > 0:
                    self.fanout = i
            elif o == "-r":
                x = float(a)
                if x > 1.:
                    self.threshold = x
            elif o == "-l":
                self.log_file = a
            elif o == "-m":
                self.map_file = a

	# Ensure that exactly one population strategy was chosen
        if (not (self.log_file or
                 (self.time_sampler_type and self.weight_sampler_type))
            or (self.log_file and
                (self.time_sampler_type or self.weight_sampler_type))):
            print("** ERROR: exactly one strategy to populate initial epoch must be chosen.")
            self.usage()
            return True

	# No line parsing error occurred
        return False

########################################################################
def parse_sampler(cmd_str):
    """Parse command line arguments specifying sampler type and input parameters
       Example: "lognormal,1.0,10.0"
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
                print("** ERROR: `{}` cannot be converted to a float".format(p))
                sys.exit(1)
            sampler_args.append(x)

    # Error check the sampler parsed from input string
    if sampler_type not in (
            "uniform",
            "lognormal"):
        print("** ERROR: unsupported sampler type: {}".format(
            sampler_type))
        sys.exit(1)
    if len(sampler_args) != 2:
        print(("** ERROR: expected two parameters for sampler type: {},"
               " got {}").format(
            sampler_type,
            len(sampler_args)))
        sys.exit(1)

    # Return the sampler parsed from the input argument
    return sampler_type, sampler_args

########################################################################
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

########################################################################
def get_output_file_stem(params):
    """Build the file name for a given rank/node
    """

    # Assemble output file stem name based on epoch population strategy
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

########################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print("[NodeGossiper] ### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print("[NodeGossiper] Parsing command line arguments")
    params = ggParameters()
    if params.parse_command_line():
       sys.exit(1)

    # Keep track of total number of procs
    n_p = params.grid_size[0] * params.grid_size[1] * params.grid_size[2]
    if n_p < 2:
        print("** ERROR: Total number of processors ({}) must be > 1".format(n_p))
        sys.exit(1)

    # Initialize random number generator
    lbsStatistics.initialize()

    # Create an epoch and populate it
    epoch = lbsEpoch.Epoch(0, params.verbose)
    if params.log_file:
        # Populate epoch from log files and store number of objects
        n_o = epoch.populate_from_log(n_p,
                                      params.time_step,
                                      params.log_file)

    else:
        # Populate epoch pseudo-randomly
        epoch.populate_from_samplers(params.n_objects,
                                     params.time_sampler_type,
                                     params.time_sampler_parameters,
                                     params.communication_degree,
                                     params.weight_sampler_type,
                                     params.weight_sampler_parameters,
                                     n_p,
                                     params.n_processors)

        # Keep track of number of objects
        n_o = params.n_objects

    # Compute and print initial load statistics
    lbsStatistics.print_function_statistics(
        epoch.processors,
        lambda x: x.get_load(),
        "initial processor loads",
        params.verbose)

    # Instantiate runtime
    rt = lbsRuntime.Runtime(epoch, params.verbose)
    rt.execute(params.n_iterations,
               params.n_rounds,
               params.fanout,
               params.threshold)

    # Create mapping from processor to Cartesian grid
    print("[NodeGossiper] Mapping {} processors onto a {}x{}x{} rectilinear grid".format(
        n_p,
        *params.grid_size))
    grid_map = lambda x: global_id_to_cartesian(x.get_id(), params.grid_size)

    # Assemble output file name stem
    output_stem = get_output_file_stem(params)

    # Instantiate epoch to VT file writer if started from a log file
    if params.log_file:
        vt_writer = lbsLoadWriterVT.LoadWriterVT(
            epoch,
            "{}".format(output_stem),
            "vom")
        vt_writer.write(params.time_step)

    # Instantiate epoch to ExodusII file writer
    ex_writer = lbsLoadWriterExodusII.LoadWriterExodusII(
        epoch,
        grid_map,
        "{}.e".format(output_stem))
    ex_writer.write(rt.statistics,
                    rt.load_distributions,
                    rt.sent_distributions)

    # Compute and print final load statistics
    _, _, l_ave, l_max, _, _, _ = lbsStatistics.print_function_statistics(
        epoch.processors,
        lambda x: x.get_load(),
        "final processor loads",
        params.verbose)
    print("\t imbalance = {:.6g}".format(
        l_max / l_ave - 1.))

    # Report on optimal statistics
    q, r = divmod(n_o, n_p)
    ell = n_p * l_ave / n_o
    print("[NodeGossiper] Optimal load statistics for {} objects with all times = {:.6g}".format(
        n_o,
        ell))
    print("\t minimum = {:.6g}  maximum = {:.6g}".format(
        q * ell,
        (q + (1 if r else 0)) * ell))
    print("\t standard deviation = {:.6g}".format(
        ell * math.sqrt(r * (n_p - r)) / n_p))
    print("\t imbalance = {:.6g}".format(
        (n_p - r) / float(n_o) if r else 0.))

    # If this point is reached everything went fine
    print("[NodeGossiper] Process complete ###")

########################################################################
