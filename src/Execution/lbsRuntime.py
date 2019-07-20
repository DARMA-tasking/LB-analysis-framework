########################################################################
lbsRuntime_module_aliases = {}
for m in [
    "sys",
    "itertools",
    "math"
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsRuntime_module_aliases:
            globals()[lbsRuntime_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Model import lbsProcessor, lbsPhase
from IO    import lbsStatistics

########################################################################
class Runtime:
    """A class to handle the execution of the LBS
    """

    ####################################################################
    def __init__(self, e, v=False):
        """Class constructor:
        e: Phase instance
        """

        # If no LBS epoch was provided, do not do anything
        if not isinstance(e, lbsPhase.Phase):
            print("*  WARNING: Could not create a LBS runtime without an epoch")
            return
        else:
            self.epoch = e

        # Verbosity of runtime
        self.Verbose = v

        # Initialize load and sent distributions
        self.load_distributions = [map(
            lambda x: x.get_load(),
            self.epoch.processors)]
        self.sent_distributions = [self.epoch.get_edges()]

        # Compute global load and weight statistics and initialize average load
        _, l_min, self.average_load, l_max, l_var, _, _, l_imb = lbsStatistics.compute_function_statistics(
            self.epoch.processors,
            lambda x: x.get_load())
        n_w, _, w_ave, w_max, w_var, _, _, w_imb = lbsStatistics.compute_function_statistics(
            self.epoch.get_edges().values(),
            lambda x: x)

        # Initialize run statistics
        print("[RunTime] Load imbalance(0) = {:.6g}".format(
            l_imb))
        print("[RunTime] Weight imbalance(0) = {:.6g}".format(
            w_imb))
        self.statistics = {
            "minimum load"                  : [l_min],
            "maximum load"                  : [l_max],
            "load variance"                 : [l_var],
            "load imbalance"                : [l_imb],
            "number of communication edges" : [n_w],
            "average communication weight"  : [w_ave],
            "maximum communication weight"  : [w_max],
            "communication weight variance" : [w_var],
            "communication weight imbalance": [w_imb]}

    ####################################################################
    def execute(self, n_iterations, n_rounds, f, r_threshold):
        """Launch runtime execution
        n_iterations: integer number of load-balancing iterations
        n_rounds: integer number of gossiping rounds
        f: integer fanout
        r_threshold: float relative overhead threshold
        """

        # Build set of processors in the epoch
        procs = set(self.epoch.processors)

        # Perform requested number of load-balancing iterations
        for i in range(n_iterations):
            print("[RunTime] Starting iteration {}".format(
                i + 1))

            # Initialize gossip process
            print("[RunTime] Spreading underload information with fanout = {}".format(
                f))
            gossip_round = 1
            gossips = {}
            l_max = 0.

            # Iterate over all processors
            for p_snd in procs:
                # Reset underload information
                p_snd.underloaded = set()
                p_snd.underloads = {}

                # Collect message when destination list is not empty
                dst, msg = p_snd.initialize_underloads(procs, self.average_load, f)
                for p_rcv in dst:
                    gossips.setdefault(p_rcv, []).append(msg)

            # Process all messages of first round
            for p_rcv, msg_lst in gossips.items():
                map(p_rcv.process_underload_message, msg_lst)

            # Report on current status when requested
            if self.Verbose:
                for p in procs:
                    print("\tunderloaded known to processor {}: {}".format(
                        p.get_id(),
                        [p_u.get_id() for p_u in p.underloaded]))


            # Forward messages for as long as necessary and requested
            while gossip_round < n_rounds:
                # Initiate next gossiping roung
                print("[RunTime] Performing underload forwarding round {}".format(
                    gossip_round))
                gossip_round += 1
                gossips.clear()

                # Iterate over all processors
                for p_snd in procs:
                    # Check whether processor must relay previously received message
                    if p_snd.round_last_received + 1 == gossip_round:
                        # Collect message when destination list is not empty
                        dst, msg = p_snd.forward_underloads(gossip_round, procs, f)
                        for p_rcv in dst:
                            gossips.setdefault(p_rcv, []).append(msg)

                # Process all messages of first round
                for p_rcv, msg_lst in gossips.items():
                    map(p_rcv.process_underload_message, msg_lst)

                # Report on current status when requested
                if self.Verbose:
                    for p in procs:
                        print("\tunderloaded known to processor {}: {}".format(
                            p.get_id(),
                            [p_u.get_id() for p_u in p.underloaded]))

            # Transfer overloads for given relative threshold
            print("[RunTime] Transferring overloads above relative threshold of {}".format(
                r_threshold))
            n_ignored = 0
            n_transfers = 0
            n_rejects = 0

            # Iterate over processors and pick those with above threshold load
            l_thr = r_threshold * self.average_load
            for p_src in procs:
                # Skip overloaded processors unaware of underloaded ones
                if not p_src.underloads:
                    n_ignored += 1
                    continue

                # Otherwise keep track if indices of underloaded processors
                p_keys = p_src.underloads.keys()

                # Compute excess load and attempt to transfer if any
                l_src = p_src.get_load()
                l_exc = l_src - l_thr
                if l_exc > 0.:
                    # Compute empirical CMF given known underloads
                    p_cmf = p_src.compute_cmf_underloads(self.average_load)

                    # Report on picked object when requested
                    if self.Verbose:
                        print("\tproc_{} excess load = {}".format(
                            p_src.get_id(),
                            l_exc))
                        print("\tCMF_{} = {}".format(
                            p_src.get_id(),
                            p_cmf))

                    # Offload objects for as long as necessary and possible
                    obj_it = iter(p_src.objects)
                    while l_exc > 0.:
                        # Pick next object
                        try:
                            o = obj_it.next()
                        except:

                            # List of objects is exhausted, break out
                            break

                        # Pseudo-randomly select destination proc
                        p_dst = lbsStatistics.inverse_transform_sample(
                            p_keys,
                            p_cmf)

                        # Decide about proposed transfer
                        l_o = o.get_time()
                        # Use criterion 6
                        #if p_dst.get_load() + l_o < self.average_load:
                        # Use criterion 6'
                        if l_o < l_src - p_dst.get_load():
                            # Report on accepted object transfer when requested
                            if self.Verbose:
                                print("\t\ttransfering object {} ({}) to processor {}".format(
                                    o.get_id(),
                                    l_o,
                                    p_dst.get_id()))

                            # Transfer object and decrease excess load
                            p_src.objects.remove(o)
                            obj_it = iter(p_src.objects)
                            p_dst.objects.add(o)
                            l_exc -= l_o
                            n_transfers +=1
                        else:
                            # Transfer was declined
                            n_rejects +=1

                            # Report on rejected object transfer when requested
                            if self.Verbose:
                                print("\t\tprocessor {2} declined transfer of object {0} ({1})".format(
                                    o.get_id(),
                                    l_o,
                                    p_dst.get_id()))

            # Edges cache is no longer current
            self.epoch.invalidate_edges()

            # Report about what happened in that iteration
            print("[RunTime] {} processors did not participate".format(
                n_ignored))
            n_proposed = n_transfers + n_rejects
            if n_proposed:
                print("[RunTime] {} transfers occurred, {} were rejected ({}% of total)".format(
                    n_transfers,
                    n_rejects,
                    100. * n_rejects / n_proposed))
            else:
                print("[RunTime] no transfers were proposed")

            # Append new load and sent distributions to existing lists
            self.load_distributions.append(map(
                lambda x: x.get_load(),
                self.epoch.get_processors()))
            self.sent_distributions.append(self.epoch.get_edges())

            # Compute and store global processor load and link weight statistics
            _, l_min, _, l_max, l_var, _, _, l_imb = lbsStatistics.compute_function_statistics(
                self.epoch.processors,
                lambda x: x.get_load())
            n_w, _, w_ave, w_max, w_var, _, _, w_imb = lbsStatistics.compute_function_statistics(
                self.epoch.get_edges().values(),
                lambda x: x)
            self.statistics["minimum load"].append(l_min)
            self.statistics["maximum load"].append(l_max)
            self.statistics["load variance"].append(l_var)
            self.statistics["load imbalance"].append(l_imb)
            self.statistics["number of communication edges"].append(n_w)
            self.statistics["average communication weight"].append(w_ave)
            self.statistics["maximum communication weight"].append(w_max)
            self.statistics["communication weight variance"].append(w_var)
            self.statistics["communication weight imbalance"].append(w_imb)

            # Report partial statistics
            iteration = i + 1
            print("[RunTime] Load imbalance({}) = {:.6g}; "
                   "min={:.6g}, max={:.6g}, ave={:.6g}, std={:.6g}").format(
                iteration,
                l_imb,
                l_min,
                l_max,
                self.average_load,
                math.sqrt(l_var))
            print("[RunTime] Weight imbalance({}) = {:.6g}; "
                   "number={:.6g}, max={:.6g}, ave={:.6g}, std={:.6g}").format(
                iteration,
                w_imb,
                n_w,
                w_max,
                w_ave,
                math.sqrt(w_var))

########################################################################
