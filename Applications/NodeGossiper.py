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
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

if __name__ == '__main__':
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from Model     import lbsEpoch
        from Execution import lbsRuntime
        from IO        import lbsLoadWriter, lbsStatistics
    else:
        from ..Model     import lbsEpoch
        from ..Execution import lbsRuntime
        from ..IO        import lbsLoadWriter, lbsStatistics

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

        # Object time sampler type
        self.time_sampler = "uniform"

        # Size of subset to which objects are initially mapped (0 = all)
        self.n_processors = 0

        # Number of gossiping rounds
        self.n_rounds = 1

        # Fan-out factor for information spreading (gossiping)
        self.fanout = 1

        # Relative overload threshold for load transfer
        self.threshold = 1.

    ####################################################################
    def usage(self):
        """Provide online help
        """

        print "Usage:"
        print "\t [-n <ni>]   number of load-balancing iterations"
        print "\t [-x <npx>]  number of procs in x direction"
        print "\t [-y <npy>]  number of procs in y direction"
        print "\t [-z <npz>]  number of procs in z direction"
        print "\t [-o <no>]   number of objects"
        print "\t [-p <np>]   number of initially used processors"
        print "\t [-k <nr>]   number of gossiping rounds"
        print "\t [-f <fo>]   gossiping fan-out value"
        print "\t [-t <rt>]   overload relative threshold"
        print "\t [-s <st>]   time sampler (uniform or lognormal)"
        print "\t [-v]        make standard output more verbose"
        print "\t [-h]        help: print this message and exit"

    ####################################################################
    def parse_command_line(self):
        """Parse command line and fill grid gossiper parameters
        """

        # Try to hash command line with respect to allowable flags
        try:
            opts, args = getopt.getopt(sys.argv[1:], "f:hk:n:o:p:s:t:vx:y:z:")
        except getopt.GetoptError:
            print "*  WARNING: incorrect command line arguments. Ignoring those."
            self.usage()
            return

        # Parse arguments and assign corresponding member variable values
        for o, a in opts:
            try:
                i = int(a)
            except:
                i = None
            if o == "-h":
                self.usage()
                return
            elif o == "-v":
                self.verbose = True
            elif o == "-n":
                if i > 0:
                    self.n_iterations = i
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
            elif o == "-s":
                if a.lower() in ("uniform", "lognormal"):
                    self.time_sampler = a.lower()
            elif o == "-k":
                if i > 0:
                    self.n_rounds = i
            elif o == "-f":
                if i > 0:
                    self.fanout = i
            elif o == "-t":
                x = float(a)
                if x > 1.:
                    self.threshold = x

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
def print_statistics(procs, key, verb=False):
    """Compute some load statistics and print to standard output
    """

    # Key starts the sentence
    key = key.title()

    # Compute statistics
    n_proc, l_min, l_ave, l_max, l_var = lbsStatistics.compute_function_statistics(
        procs,
        lambda x: x.get_load())

    # Print detailed load information if requested
    if verb:
        print "[NodeGossiper] {} processor loads:".format(key)
        for p in procs:
            print "\t proc_{} load = {}".format(p.get_id(), p.get_load())

    # Always print summary
    print "[NodeGossiper] {} processor loads: min={:.6g} mean={:.6g} max={:.6g} stdev={:.6g}".format(
        key,
        l_min,
        l_ave,
        l_max,
        math.sqrt(l_var))

########################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print "[NodeGossiper] ### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro)

    # Instantiate parameters and set values from command line arguments
    print "[NodeGossiper] Parsing command line arguments"
    params = ggParameters()
    params.parse_command_line()

    # Initialize random number generator
    lbsStatistics.initialize()

    # Create an epoch and randomly generate it
    epoch = lbsEpoch.Epoch()
    if params.time_sampler == "uniform":
        sampler_params = [1.e-5, 1.e-1]
    elif params.time_sampler == "lognormal":
        sampler_params = [5.0005e-2, 8.33e-4]
    else:
        print "** ERROR: unsupported sampler type {}".format(params.time_sampler)

    n_p = params.grid_size[0] * params.grid_size[1] * params.grid_size[2]
    epoch.populate_from_sampler(params.n_objects,
                                params.time_sampler,
                                sampler_params,
                                n_p,
                                params.n_processors)

    # Compute and print initial load information
    print_statistics(epoch.processors,
                     "initial",
                     params.verbose)

    # Instantiate runtime
    rt = lbsRuntime.Runtime(epoch, params.verbose)
    rt.execute(params.n_iterations,
               params.n_rounds,
               params.fanout,
               params.threshold)

    # Create mapping from processor to Cartesian grid
    print "[NodeGossiper] Mapping {} processors into a {}x{}x{} rectilinear grid".format(n_p, *params.grid_size)
    grid_map = lambda x: global_id_to_cartesian(x.get_id(), params.grid_size)

    # Instantiate epoch to ExodusII file writer
    file_name = "NodeGossiper-n{}-p{}-o{}-{}-i{}-k{}-f{}-t{}.e".format(
        n_p,
        params.n_processors,
        params.n_objects,
        params.time_sampler,
        params.n_iterations,
        params.n_rounds,
        params.fanout,
        "{}".format(params.threshold).replace('.', '_'))
    writer = lbsLoadWriter.LoadWriter(epoch, grid_map, file_name)
    writer.write(rt.statistics,
                 rt.load_distributions)

    # Compute and print final load information
    print_statistics(epoch.processors,
                     "final",
                     params.verbose)

    # If this point is reached everything went fine
    print "[NodeGossiper] Process complete ###"

########################################################################
