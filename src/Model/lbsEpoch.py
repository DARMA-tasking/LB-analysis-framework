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

from Model import lbsObject, lbsProcessor
from IO    import lbsStatistics

########################################################################
class Epoch:
    """A class representing the state of collection of processors with
    objects at a given round
    """

    ####################################################################
    def __init__(self, p=[]):
        # List of processors may be passed by constructor
        self.processors = p

        # Initialize gossiping round
        self.round_index = 0

    ####################################################################
    def get_processors_ids(self):
        """Retrieve IDs of processors belonging to epoch
        """

        return [p.get_id() for p in self.processors]

    ####################################################################
    def populate_from_sampler(self, n_o, t_sampler, sampler_params, n_p, s_s=0):
        """Use sampler to populate either all or n procs in an epoch
        """

        # Retrieve desired time sampler with its theoretical average
        time_sampler, th_ave = lbsStatistics.sampler(t_sampler,
                                                     sampler_params)

        # Create n_o objects with uniformly distributed times in given range
        print "[Epoch] Creating {} objects with {} pseudo-random times".format(
            n_o,
            t_sampler)
        obj = set([lbsObject.Object(
            i,
            time_sampler()) for i in range(n_o)])

        # Compute and report object statistics
        n_proc, t_min, t_mean, t_max, t_var, t_skw, t_krt = lbsStatistics.compute_function_statistics(
            obj,
            lambda x: x.get_time())
        print "[Epoch] Object times: min={:.6g} mean={:.6g} max={:.6g} stdev={:.6g} skew={:.6g} kurtex={:.6g}".format(
            t_min,
            t_mean,
            t_max,
            math.sqrt(t_var),
            t_skw,
            t_krt - 3)

        # Create n_p processors
        self.processors = [lbsProcessor.Processor(i) for i in range(n_p)]

        if s_s and s_s <= n_p:
            print "[Epoch] Randomly assigning objects to {} processors amongst {}".format(s_s, n_p)
        else:
            # Sanity check
            if s_s > n_p:
                print "*  WARNING: too many processors ({}) requested: only {} available.".format(s_s, n_p)
                s_s = n_p
            print "[Epoch] Randomly assigning objects to {} processors".format(n_p)

        # Randomly assign objects to processors
        if s_s > 0:
            # Randomly assign objects to a subset o processors of size s_s
            proc_list = rnd.sample(self.processors, s_s)
            for o in obj:
                rnd.choice(proc_list).add_object(o)
        else:
            # Randomly assign objects to all processors
            for o in obj:
                rnd.choice(self.processors).add_object(o)

        # Compute and output global statistics
        print "[Epoch] Average object time: {} (theoretical: {})".format(
            lbsStatistics.compute_function_mean(obj, lambda x: x.get_time()),
            th_ave)

########################################################################
