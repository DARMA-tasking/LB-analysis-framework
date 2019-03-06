########################################################################
lbsLoadWriter_module_aliases = {}
for m in [
    "csv",
    "sys",
    "os",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsLoadWriter_module_aliases:
            globals()[lbsLoadWriter_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

from Model import lbsObject, lbsProcessor

########################################################################
class LoadReader:
    """A class to read VT's load stats output files. These CSV files conform
    to the following format:

      <iter/phase>, <object-id>, <time>
      <iter/phase>, <object-id1>, <object-id2>, <num-bytes>

    Each file is named as <base-name>.<node>.out, where <node> spans the number
    of MPI ranks that VT is utilizing.

    Each line in a given file specifies the load of each object that is
    currently mapped to that VT node for a given iteration/phase. Lines with 3
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
    def node_file_name(self, node):
        """Build the file name for a given rank/node
        """
        return str(self.file_prefix) + "." + str(node) + ".out"

    ####################################################################
    def read(self, node, doiter=-1):
        """Read the file for a given node/rank. If doiter==-1 then all iterations
        are read; else, only the iteration 'doiter' is read from the file.
        """

        iter_map = dict()
        fname = self.node_file_name(node)

        if self.debug_mode:
            print "[LoadReader] Reading file: {}".format(fname)

        if not os.path.isfile(fname):
            print "** ERROR: [LoadReader] file='{}' does not exist.".format(fname)
            sys.exit(1)

        with open(fname, 'r') as f:
            log = csv.reader(f, delimiter=',')
            for row in log:
                entries = len(row)
                if entries == 3:
                    # Parsing the three-entry case, thus this format:
                    #   <iter/phase>, <object-id>, <time>
                    (iter,id,time) = row

                    # Convert these into integers and float before using them or
                    # inserting the values in the dictionary
                    iter = int(iter)
                    id   = int(id)
                    time = float(time)

                    if int(iter) == doiter or doiter == -1:
                        obj = lbsObject.Object(id,time,iter)

                        if not iter in iter_map:
                            iter_map[iter] = lbsProcessor.Processor(node)

                        iter_map[iter].add_object(obj)

                        if self.debug_mode:
                            print "[LoadReader] iter={},id={},time={}".format(iter,id,time)
                elif entries == 4:
                    # @todo parse the four-entry case for communication
                    print "** ERROR: [LoadReader] comm graph unimplemented"
                    sys.exit(1)
                else:
                    print "** ERROR: [LoadReader] '{}' wrong len.".format(row)
                    sys.exit(1)

        if self.debug_mode:
            print "[LoadReader] Finished reading file: {}".format(fname)

        return iter_map

    ####################################################################
    def read_iter(self, n_p, iter=0):
        """Read all the data in the range of procs [0..n_p) for a given
        iteration `iter`. Collapse the iter_map dictionary from `read(..)` into
        a list of processors to be returned for the given iteration.
        """
        procs = [None] * n_p
        for p in range(n_p):
            proc_iter_map = self.read(p, iter)
            procs[p] = proc_iter_map[iter]
        return procs

########################################################################
