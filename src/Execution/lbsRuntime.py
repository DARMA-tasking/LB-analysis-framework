#
#@HEADER
###############################################################################
#
#                                 lbsRuntime.py
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
########################################################################
lbsRuntime_module_aliases = {}
for m in [
    "bcolors",
    "math",
    "sys",
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
        print("** ERROR: failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Model      import lbsProcessor, lbsPhase
from IO         import lbsStatistics
from Execution  import lbsCriterionBase

########################################################################
class Runtime:
    """A class to handle the execution of the LBS
    """

    ####################################################################
    def __init__(self, p, c, a=False, v=False):
        """Class constructor:
        p: Phase instance
        c: criterion index
        a: use actual destination load [FALSE/True]
        v: verbose mode [FALSE/True]
        """

        # If no LBS phase was provided, do not do anything
        if not isinstance(p, lbsPhase.Phase):
            print(bcolors.WARN
                + "*  WARNING: Could not create a LBS runtime without a phase"
                + bcolors.END)
            return
        else:
            self.phase = p

        # Use of actual destination load when relevant for criterion
        self.actual_dst_load = a

        # Verbosity of runtime
        self.verbose = v

        # Transfer critertion index
        self.Criterion = c

        # Initialize load and sent distributions
        self.load_distributions = [[
            p.get_load() for p in self.phase.processors]]
        self.sent_distributions = [{
            k:v for k,v in self.phase.get_edges().items()}]

        # Compute global load and weight statistics and initialize average load
        _, l_min, self.average_load, l_max, l_var, _, _, l_imb = lbsStatistics.compute_function_statistics(
            self.phase.processors,
            lambda x: x.get_load())
        n_w, _, w_ave, w_max, w_var, _, _, w_imb = lbsStatistics.compute_function_statistics(
            self.phase.get_edges().values(),
            lambda x: x)

        # Initialize run statistics
        print(bcolors.HEADER
            + "[RunTime] "
            + bcolors.END
            + "Load imbalance(0) = {:.6g}".format(
            l_imb))
        print(bcolors.HEADER
            + "[RunTime] "
            + bcolors.END
            + "Weight imbalance(0) = {:.6g}".format(
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

        # Build set of processors in the phase
        procs = set(self.phase.processors)

        # Perform requested number of load-balancing iterations
        for i in range(n_iterations):
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Starting iteration {}".format(
                i + 1))

            # Initialize gossip process
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Spreading underload information with fanout = {}".format(
                f))
            gossip_round = 1
            gossips = {}
            l_max = 0.

            # Iterate over all processors
            for p_snd in procs:
                # Reset underload information known by sender
                p_snd.reset_all_load_information()

                # Collect message when destination list is not empty
                dst, msg = p_snd.initialize_underloads(procs, self.average_load, f)
                for p_rcv in dst:
                    gossips.setdefault(p_rcv, []).append(msg)

            # Process all messages of first round
            for p_rcv, msg_lst in gossips.items():
                for m in msg_lst:
                    p_rcv.process_underload_message(m)

            # Report on gossiping status when requested
            if self.verbose:
                for p in procs:
                    print("\tunderloaded known to processor {}: {}".format(
                        p.get_id(),
                        [p_u.get_id() for p_u in p.get_known_underloaded()]))

            # Forward messages for as long as necessary and requested
            while gossip_round < n_rounds:
                # Initiate next gossiping roung
                print(bcolors.HEADER
                    + "[RunTime] "
                    + bcolors.END
                    + "Performing underload forwarding round {}".format(
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
                    for m in msg_lst:
                        p_rcv.process_underload_message(m)

                # Report on gossiping status when requested
                if self.verbose:
                    for p in procs:
                        print("\tunderloaded known to processor {}: {}".format(
                            p.get_id(),
                            [p_u.get_id() for p_u in p.get_known_underloaded()]))

            # Determine overload threshold
            l_thr = r_threshold * self.average_load

            # Build reverse lookup of underloaded to overloaded viewers
            for p in procs:
                # Skip non-overloaded processors
                if not p.get_load() - l_thr > 0.:
                    continue

                # Update viewers on underloaded processors known to this one
                p.add_as_overloaded_viewer(p.get_known_underloaded())
                
            # Report on viewers of underloaded processors
            viewers_counts = {}
            for p in procs:
                # Skip non underloaded processors
                if not p.get_load() < self.average_load:
                    continue

                # Retrieve cardinality of viewers
                viewers = p.get_overloaded_viewers()
                viewers_counts[p] = len(viewers)

                # Report on viewers of underloaded processor when requested
                if self.verbose:
                    print("\toverloaded viewers of processor {}: {}".format(
                        p.get_id(),
                        [p_o.get_id() for p_o in viewers]))

            # Report viewers counts to underloaded processors
            n_u, v_min, v_ave, v_max, _, _, _, _ = lbsStatistics.compute_function_statistics(
                viewers_counts.values(),
                lambda x: x)
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Reporting viewers counts (min:{}, mean: {:.3g} max: {}) to {} underloaded processors".format(
                      v_min,
                      v_ave,
                      v_max,
                      n_u))

            # Initialize transfer step
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Migrating overloads above relative threshold of {}".format(
                r_threshold))
            n_ignored, n_transfers, n_rejects = 0, 0, 0

            # Instantiate object transfer criterion
            transfer_criterion = lbsCriterionBase.CriterionBase.factory(
                self.Criterion,
                procs,
                self.phase.get_edges(),
                {"average_load": self.average_load,
                 "actual_destination_load": self.actual_dst_load})
            if not transfer_criterion:
                print(bcolors.ERR
                    + "*  ERROR: cannot load-balance without a load transfer criterion"
                    + bcolors.END)
                sys.exit(1)

            # Iterate over processors and pick those with above threshold load
            for p_src in procs:
                # Skip non-overloaded processors
                l_exc = p_src.get_load() - l_thr
                if not l_exc > 0.:
                    continue

                # Skip overloaded processors unaware of underloaded ones
                underloads = p_src.get_known_underloads()
                if not underloads:
                    n_ignored += 1
                    continue

                # Offload objects for as long as necessary and possible
                obj_it = iter(p_src.objects)
                while l_exc > 0.:
                    # Leave this processor if it ran out of known underloaded
                    p_keys = list(p_src.get_known_underloads().keys())
                    if not p_keys:
                        break

                    # Pick next object
                    try:
                        o = next(obj_it)
                    except:
                        # List of objects is exhausted, break out
                        break

                    # Compute empirical CMF given known underloads
                    p_cmf = p_src.compute_cmf_underloads(self.average_load)

                    # Pseudo-randomly select destination proc
                    p_dst = lbsStatistics.inverse_transform_sample(
                        p_keys,
                        p_cmf)

                    # Report on overloaded processor when requested
                    if self.verbose:
                        print("\texcess load of processor {}: {}".format(
                            p_src.get_id(),
                            l_exc))
                        print("\tknown underloaded processors: {}".format(
                            [u.get_id() for u in underloads]))
                        print("\tCMF_{} = {}".format(
                            p_src.get_id(),
                            p_cmf))

                    # Decide about proposed transfer
                    if transfer_criterion.compute(o, p_src, p_dst) < 0.:
                        # Reject proposed transfer
                        n_rejects += 1

                        # Report on rejected object transfer when requested
                        if self.verbose:
                            print("\t\tprocessor {} declined transfer of object {} ({})".format(
                                p_dst.get_id(),
                                o.get_id(),
                                o.get_time()))
                    else:
                        # Accept proposed transfer
                        if self.verbose:
                            print("\t\tmigrating object {} ({}) to processor {}".format(
                                o.get_id(),
                                o.get_time(),
                                p_dst.get_id()))

                        # Transfer object
                        if p_dst not in p_src.known_underloads:
                            print(p_src, p_dst)
                            print(p_src.get_id(), p_dst.get_id())
                            print(sorted([p.get_id() for p in p_src.known_underloads]))
                            print(sorted([p.get_id() for p in p_keys]))
                            sys.exit(1)
                        l_exc -= p_src.remove_object(o, p_dst)
                        obj_it = iter(p_src.objects)
                        p_dst.add_object(o, self.average_load)
                        n_transfers += 1
 
            # Invalidate cache of edges
            self.phase.invalidate_edge_cache()
            print(bcolors.HEADER
                  + "[RunTime] "
                  + bcolors.END
                  + "Iteration complete ({} skipped processors)".format(
                      n_ignored))
            n_proposed = n_transfers + n_rejects
            if n_proposed:
                print(bcolors.HEADER
                      + "[RunTime] "
                      + bcolors.END
                      + "{} proposed transfers, {} occurred, {} rejected ({:.4}%)".format(
                          n_proposed,
                          n_transfers,
                          n_rejects,
                          100. * n_rejects / n_proposed))
            else:
                print(bcolors.HEADER
                      + "[RunTime] "
                      + bcolors.END
                      + "No transfers were proposed")

            # Append new load and sent distributions to existing lists
            self.load_distributions.append([
                p.get_load() for p in self.phase.get_processors()])
            self.sent_distributions.append({
                k:v for k,v in self.phase.get_edges().items()})

            # Compute and store global processor load and link weight statistics
            _, l_min, _, l_max, l_var, _, _, l_imb = lbsStatistics.compute_function_statistics(
                self.phase.processors,
                lambda x: x.get_load())
            n_w, _, w_ave, w_max, w_var, _, _, w_imb = lbsStatistics.compute_function_statistics(
                self.phase.get_edges().values(),
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
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Load imbalance({}) = {:.6g}; min={:.6g}, max={:.6g}, ave={:.6g}, std={:.6g}".format(
                iteration,
                l_imb,
                l_min,
                l_max,
                self.average_load,
                math.sqrt(l_var)))
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Weight imbalance({}) = {:.6g}; "
                   "number={:.6g}, max={:.6g}, ave={:.6g}, std={:.6g}".format(
                iteration,
                w_imb,
                n_w,
                w_max,
                w_ave,
                math.sqrt(w_var)))

########################################################################
