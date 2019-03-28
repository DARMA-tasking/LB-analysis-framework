########################################################################
lbsLoadReaderVT_module_aliases = {}
for m in [
    "csv",
    "sys",
    "os",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsLoadReaderVT_module_aliases:
            globals()[lbsLoadReaderVT_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

from Model import lbsObject, lbsProcessor

########################################################################
class LoadReader:
    """A class to read VT Object Map files. These CSV files conform
    to the following format:

      <time_step/phase>, <object-id>, <time>
      <time_step/phase>, <object-id1>, <object-id2>, <num-bytes>

    Each file is named as <base-name>.<node>.vom, where <node> spans the number
    of MPI ranks that VT is utilizing.

    Each line in a given file specifies the load of each object that is
    currently mapped to that VT node for a given time_step/phase. Lines with 3
    entries specify load for an object in term of wall time. Lines with 4
    entries specify the communication volume between objects in bytes.

    Load profile collection and output is enabled in VT with the following flags:

      mpirun -n 4 ./program --vt_lb_stats
                            --vt_lb_stats_dir=my-stats-dir
                            --vt_lb_stats_file=<base-name>
    """

  ####################################################################
    def __init__(self, file_prefix, debug=False):
        # The base directory and file name for the log files
        self.file_prefix = file_prefix

        # Enable debug mode with extra verbosity
        self.debug_mode = debug

    ####################################################################
    def get_node_trace_file_name(self, node_id):
        """Build the file name for a given rank/node ID
        """

        return "{}.{}.vom".format(
            self.file_prefix, node_id)

    ####################################################################
    def read(self, node_id, time_step=-1, comm=False):
        """Read the file for a given node/rank. If time_step==-1 then all
        steps are read from the file; otherwise, only `time_step` is.
        """

        # Retrieve file name for given node and make sure that it exists
        file_name = self.get_node_trace_file_name(node_id)
        print "[LoadReaderVT] Reading {} VT object map".format(file_name)
        if not os.path.isfile(file_name):
            print "** ERROR: [LoadReaderVT] File {} does not exist.".format(file_name)
            sys.exit(1)

        # Initialize storage
        iter_map = dict()

        # Open specified input file
        with open(file_name, 'r') as f:
            log = csv.reader(f, delimiter=',')
            # Iterate over rows of input file
            for row in log:
                n_entries = len(row)

                # Handle three-entry case
                if n_entries == 3:
                    # Parsing the three-entry case, thus this format:
                    #   <time_step/phase>, <object-id>, <time>
                    # Converting these into integers and float before using them or
                    # inserting the values in the dictionary
                    try:
                        phase, o_id = map(int, row[:2])
                        time = float(row[2])
                    except:
                        print "** ERROR: [LoadReaderVT] Incorrect row format:".format(row)

                    # Update processor if iteration was requested
                    if time_step in (phase, -1):
                        # Instantiate object with retrieved parameters
                        obj = lbsObject.Object(o_id, time, node_id)

                        # If this iteration was never encoutered initialize proc object
                        iter_map.setdefault(phase, lbsProcessor.Processor(node_id))

                        # Add object to processor
                        iter_map[phase].add_object(obj)

                        # Print debug information when requested
                        if self.debug_mode:
                            print "[LoadReaderVT] iteration = {}, object id = {}, time = {}".format(
                                phase,
                                o_id,
                                time)

                # Handle four-entry case
                elif n_entries == 4:
                    # @todo parse the four-entry case for communication
                    print "** ERROR: [LoadReaderVT] Comm graph unimplemented"
                    sys.exit(1)
                else:
                    print "** ERROR: [LoadReaderVT] Wrong length: {}".format(row)
                    sys.exit(1)

        # Print debug information when requested
        if self.debug_mode:
            print "[LoadReaderVT] Finished reading file: {}".format(file_name)

        # Return map of populated processors per iteration
        return iter_map

    ####################################################################
    def read_iteration(self, n_p, time_step):
        """Read all the data in the range of procs [0..n_p) for a given
        iteration `time_step`. Collapse the iter_map dictionary from `read(..)`
        into a list of processors to be returned for the given iteration.
        """
        
        # Create storage for processors
        procs = [None] * n_p

        # Iterate over all processors
        for p in range(n_p):
            # Read data for given iteration and assign it to processor
            proc_iter_map = self.read(p, time_step)

            # Try to retrieve processor information at given time-step
            try:
                procs[p] = proc_iter_map[time_step]
            except KeyError:
                print "** ERROR: [LoadReaderVT] Could not retrieve information for processor {} at time_step {}".format(
                    p,
                    time_step)
                sys.exit(1)
            
        # Return populated list of processors
        return procs

########################################################################
