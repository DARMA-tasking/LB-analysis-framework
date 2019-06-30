########################################################################
lbsEpoch_module_aliases = {
    "random": "rnd",
    }
for m in [
    "random",
    "math",
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsEpoch_module_aliases:
            globals()[lbsEpoch_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

from Model import lbsObject, lbsProcessor, lbsObjectCommunicator, lbsEdge
from IO    import lbsStatistics, lbsLoadReaderVT

########################################################################
class Epoch:
    """A class representing the state of collection of processors with
    objects at a given round
    """

    ####################################################################
    def __init__(self, t=0, verbose=False):
        # Initialize empty list of processors
        self.processors = []

        # Default time-step/phase of this epoch
        self.time_step = t

        # Initialize gossiping round
        self.round_index = 0

        # Enable or disable verbose mode
        self.verbose = verbose

    ####################################################################
    def get_processors_ids(self):
        """Retrieve IDs of processors belonging to epoch
        """

        return [p.get_id() for p in self.processors]

    ####################################################################
    def get_time_step(self):
        """Retrieve the time-step/phase for this epoch
        """

        return self.time_step

    ####################################################################
    def populate_from_sampler(self, n_o, ts, tsp, c_degree, cs, csp, n_p, s_s=0):
        """Use sampler to populate either all or n procs in an epoch
        """

        # Retrieve desired time sampler with its theoretical average
        time_sampler, sampler_name = lbsStatistics.sampler(ts, tsp)

        # Create n_o objects with uniformly distributed times in given range
        print "[Epoch] Creating {} objects with times sampled from {}".format(
            n_o,
            sampler_name)

        # Decide whether edges and communications must be created
        if c_degree > 0:
            # Retrieve desired communication weight sampler with its theoretical average
            weight_sampler, weight_sampler_name = lbsStatistics.sampler(cs, csp)

            print "[Epoch] Creating {} objects with communication weights sampled from {}".format(
                n_o,
                weight_sampler_name)

            # Maker object edges with provided sampler for given degree
            make_edges = lambda obj_id, edge_pop: { edge_pop[i]:lbsEdge.Edge(
                obj_id,
                edge_pop[i],
                weight_sampler()) for i in range(c_degree) }

            # Make ojbect communicators with given weight
            make_communicators = lambda out: lbsObjectCommunicator.ObjectCommunicator([], out)
        else:
            # Otherwise neither edges nor communicators are created
            make_edges = lambda i, edge_pop: None
            make_communicators = lambda i: None

        # Create set of objects with given makers
        objects = set([lbsObject.Object(
            i,
            time_sampler(),
            None,
            make_communicators(make_edges(
                i,
                rnd.sample([i for i in range(n_o)],
                           c_degree)))
            ) for i in range(n_o)])

        # Print more information when requested
        if self.verbose:
            for obj in objects:
                comm = obj.get_communicator()
                print "[Epoch] i={}, edges={}".format(
                    obj.get_id(),
                    comm.get_out_edges() if comm else None
                    )
                if comm:
                    for _, v in comm.get_out_edges().items():
                        print "in={}, out={}, weight={}".format(
                            v.get_send_obj(),
                            v.get_recv_obj(),
                            v.get_weight())

        # Compute and report object statistics
        lbsStatistics.print_function_statistics(objects,
                                                lambda x: x.get_time(),
                                                "object times")

        # Create n_p processors
        self.processors = [lbsProcessor.Processor(i) for i in range(n_p)]

        # Randomly assign objects to processors
        if s_s and s_s <= n_p:
            print "[Epoch] Randomly assigning objects to {} processors amongst {}".format(s_s, n_p)
        else:
            # Sanity check
            if s_s > n_p:
                print "*  WARNING: too many processors ({}) requested: only {} available.".format(s_s, n_p)
                s_s = n_p
            print "[Epoch] Randomly assigning objects to {} processors".format(n_p)
        if s_s > 0:
            # Randomly assign objects to a subset o processors of size s_s
            proc_list = rnd.sample(self.processors, s_s)
            for o in objects:
                p = rnd.choice(proc_list)
                p.add_object(o)
                o.first = p.get_id()
        else:
            # Randomly assign objects to all processors
            for o in objects:
                p = rnd.choice(self.processors)
                p.add_object(o)
                o.first = p.get_id()

    ####################################################################
    def populate_from_log(self, n_p, t_s, basename):
        """Populate this epoch by reading in a load profile from log files
        """

        # Instantiate VT load reader
        reader = lbsLoadReaderVT.LoadReader(basename)

        # Populate epoch with reader output
        print "[Epoch] Reading objects from time-step {} of VOM files with prefix {}".format(
            t_s,
            basename)
        self.processors = reader.read_iteration(n_p, t_s)
        
        # Compute and report object statistics
        objects = set()
        for p in self.processors:
            objects = objects.union(p.objects)
        lbsStatistics.print_function_statistics(objects,
                                                lambda x: x.get_time(),
                                                "object times")
        # Return number of found objects
        return len(objects)

########################################################################
