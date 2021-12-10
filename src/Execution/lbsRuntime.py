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

from bisect import bisect
from itertools import accumulate
import math
import sys
from typing import Union

import bcolors

from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsPhase import Phase
from src.IO.lbsStatistics import compute_function_statistics, inverse_transform_sample


class Runtime:
    """A class to handle the execution of the LBS
    """

    def __init__(self, p, c: dict, order_strategy: str, a=False, v=False):
        """Class constructor:
        p: phase instance
        c: dictionary with riterion name and optional parameters
        order_strategy: Objects order strategy
        a: use actual destination load [FALSE/True]
        v: verbose mode [FALSE/True]
        """

        # If no LBS phase was provided, do not do anything
        if not isinstance(p, Phase):
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

        # Transfer critertion type and parameters
        self.criterion_name = c.get("name")
        self.criterion_params = c.get("parameters", {})

        # Initialize load and sent distributions
        self.load_distributions = [[
            p.get_load() for p in self.phase.ranks]]
        self.sent_distributions = [{
            k:v for k,v in self.phase.get_edges().items()}]

        # Compute global load and weight statistics and initialize average load
        _, l_min, self.average_load, l_max, l_var, _, _, l_imb = compute_function_statistics(
            self.phase.ranks,
            lambda x: x.get_load())
        n_w, _, w_ave, w_max, w_var, _, _, w_imb = compute_function_statistics(
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

        # Initialize strategy
        self.strategy_mapped = {
            "arbitrary": self.arbitrary,
            "element_id": self.element_id,
            "fewest_migrations": self.fewest_migrations,
            "small_objects": self.small_objects,
            "largest_objects": self.largest_objects}
        self.order_strategy = self.strategy_mapped.get(order_strategy, None)

    def propagate_information(self, n_rounds, f):
        """Execute information phase
        n_rounds: integer number of gossiping rounds
        f: integer fanout
        """

        # Build set of all ranks in the phase
        rank_set = set(self.phase.get_ranks())

        # Initialize gossip process
        print(bcolors.HEADER
            + "[RunTime] "
            + bcolors.END
            + "Spreading load information with fanout = {}".format(
            f))
        gossip_round = 1
        gossips = {}
        l_max = 0.

        # Iterate over all ranks
        for p_snd in rank_set:
            # Reset load information known by sender
            p_snd.reset_all_load_information()

            # Collect message when destination list is not empty
            dst, msg = p_snd.initialize_loads(rank_set, f)
            for p_rcv in dst:
                gossips.setdefault(p_rcv, []).append(msg)

        # Process all messages of first round
        for p_rcv, msg_lst in gossips.items():
            for m in msg_lst:
                p_rcv.process_load_message(m)

        # Report on gossiping status when requested
        if self.verbose:
            for p in rank_set:
                print("\tloaded known to rank {}: {}".format(
                    p.get_id(),
                    [p_u.get_id() for p_u in p.get_known_loaded()]))

        # Forward messages for as long as necessary and requested
        while gossip_round < n_rounds:
            # Initiate next gossiping roung
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Performing load forwarding round {}".format(
                gossip_round))
            gossip_round += 1
            gossips.clear()

            # Iterate over all ranks
            for p_snd in rank_set:
                # Check whether rank must relay previously received message
                if p_snd.round_last_received + 1 == gossip_round:
                    # Collect message when destination list is not empty
                    dst, msg = p_snd.forward_loads(gossip_round, rank_set, f)
                    for p_rcv in dst:
                        gossips.setdefault(p_rcv, []).append(msg)

            # Process all messages of first round
            for p_rcv, msg_lst in gossips.items():
                for m in msg_lst:
                    p_rcv.process_load_message(m)

            # Report on gossiping status when requested
            if self.verbose:
                for p in rank_set:
                    print("\tloaded known to rank {}: {}".format(
                        p.get_id(),
                        [p_u.get_id() for p_u in p.get_known_loaded()]))

        # Build reverse lookup of loaded to overloaded viewers
        for p in rank_set:
            # Skip non-loaded ranks
            if not p.get_load():
                continue

            # Update viewers on loaded ranks known to this one
            p.add_as_viewer(p.get_known_loaded())

        # Report on viewers of loaded ranks
        viewers_counts = {}
        for p in rank_set:
            # Skip non loaded ranks
            if not p.get_load():
                continue

            # Retrieve cardinality of viewers
            viewers = p.get_viewers()
            viewers_counts[p] = len(viewers)

            # Report on viewers of loaded rank when requested
            if self.verbose:
                print("\tviewers of rank {}: {}".format(
                    p.get_id(),
                    [p_o.get_id() for p_o in viewers]))

        # Report viewers counts to loaded ranks
        n_u, v_min, v_ave, v_max, _, _, _, _ = compute_function_statistics(
            viewers_counts.values(),
            lambda x: x)
        print(bcolors.HEADER
            + "[RunTime] "
            + bcolors.END
            + "Reporting viewers counts (min:{}, mean: {:.3g} max: {}) to {} loaded ranks".format(
                  v_min,
                  v_ave,
                  v_max,
                  n_u))

    def execute(self, n_iterations, n_rounds, f, r_threshold, pmf_type):
        """Launch runtime execution
        n_iterations: integer number of load-balancing iterations
        n_rounds: integer number of gossiping rounds
        f: integer fanout
        r_threshold: float relative overhead threshold
        pmf_type: 0: modified original approach; 1: NS variant 
        """

        # Perform requested number of load-balancing iterations
        for i in range(n_iterations):
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Starting iteration {}".format(
                i + 1))

            # Start with information phase
            self.propagate_information(n_rounds, f)

            # Initialize transfer step
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Migrating overloads above relative threshold of {}".format(
                r_threshold))
            n_ignored, n_transfers, n_rejects = 0, 0, 0

            # Instantiate object transfer criterion
            self.criterion_params.update(
                {"average_load": self.average_load,
                 "actual_destination_load": self.actual_dst_load})
            transfer_criterion = CriterionBase.factory(
                self.criterion_name,
                set(self.phase.get_ranks()),
                self.phase.get_edges(),
                self.criterion_params)
            if not transfer_criterion:
                print(bcolors.ERR
                    + "*  ERROR: cannot load-balance without a load transfer criterion"
                    + bcolors.END)
                sys.exit(1)

            # Iterate over rank
            for p_src in self.phase.get_ranks():
                # Skip non-loaded ranks
                if not p_src.get_load() > 0.:
                    continue

                # Skip ranks unaware of loaded peers
                loads = p_src.get_known_loads()
                if not loads:
                    n_ignored += 1
                    continue

                # Offload objects for as long as necessary and possible
                srt_proc_obj = self.order_strategy(
                    objects=p_src. migratable_objects)
                obj_it = iter(srt_proc_obj)
                while p_src.get_load() > self.average_load:
                    # Leave this rank if it ran out of known loaded
                    p_keys = list(p_src.get_known_loads().keys())
                    if not p_keys:
                        break

                    # Pick next object
                    try:
                        o = next(obj_it)
                    except:
                        # List of objects is exhausted, break out
                        break

                    # Compute empirical CMF given known loads
                    p_cmf = p_src.compute_cmf_loads()

                    # Pseudo-randomly select destination proc
                    p_dst = inverse_transform_sample(
                        p_keys,
                        p_cmf)

                    # Report on overloaded rank when requested
                    if self.verbose:
                        print("\texcess load of rank {}: {}".format(
                            p_src.get_id(),
                            l_exc))
                        print("\tknown loaded ranks: {}".format(
                            [u.get_id() for u in loads]))
                        print("\tCMF_{} = {}".format(
                            p_src.get_id(),
                            p_cmf))

                    # Decide about proposed transfer
                    if transfer_criterion.compute(o, p_src, p_dst) < 0.:
                        # Reject proposed transfer
                        n_rejects += 1

                        # Report on rejected object transfer when requested
                        if self.verbose:
                            print("\t\trank {} declined transfer of object {} ({})".format(
                                p_dst.get_id(),
                                o.get_id(),
                                o.get_time()))
                    else:
                        # Accept proposed transfer
                        if self.verbose:
                            print("\t\tmigrating object {} ({}) to rank {}".format(
                                o.get_id(),
                                o.get_time(),
                                p_dst.get_id()))

                        # Transfer object
                        if p_dst not in p_src.known_loads:
                            print(p_src, p_dst)
                            print(p_src.get_id(), p_dst.get_id())
                            print(sorted([p.get_id() for p in p_src.known_loads]))
                            print(sorted([p.get_id() for p in p_keys]))
                            sys.exit(1)
                        p_src.remove_migratable_object(o, p_dst)
                        obj_it = iter(p_src.get_migratable_objects())
                        p_dst.add_migratable_object(o)
                        n_transfers += 1
 
            # Invalidate cache of edges
            self.phase.invalidate_edge_cache()
            print(bcolors.HEADER
                  + "[RunTime] "
                  + bcolors.END
                  + "Iteration complete ({} skipped ranks)".format(
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
                p.get_load() for p in self.phase.get_ranks()])
            self.sent_distributions.append({
                k:v for k,v in self.phase.get_edges().items()})

            # Compute and store global rank load and link weight statistics
            _, l_min, self.load_average, l_max, l_var, _, _, l_imb = compute_function_statistics(
                self.phase.ranks,
                lambda x: x.get_load())
            n_w, _, w_ave, w_max, w_var, _, _, w_imb = compute_function_statistics(
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
                self.load_average,
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

    @staticmethod
    def sort(objects: set, key):
        return sorted(list(objects), key=key)

    def sorted_ascending(self, objects: Union[set, list]):
        return self.sort(objects, key=lambda x: x.get_time())

    def sorted_descending(self, objects: Union[set, list]):
        return self.sort(objects, key=lambda x: -x.get_time())

    @staticmethod
    def arbitrary(objects: set):
        """ Random strategy. Objects are passed without any order. """
        return objects

    def element_id(self, objects: set):
        """ Objects ordered by ID. """
        return self.sort(objects, key=lambda x: x.get_id())

    def load_ex(self, objects: set):
        proc_load = sum([obj.get_time() for obj in objects])
        return proc_load - self.average_load

    def fewest_migrations(self, objects: set):
        """ First find the load of the smallest single object that, if migrated
            away, could bring this rank's load below the target load.
            Sort largest to smallest if <= load_ex
            Sort smallest to largest if > load_ex
        """
        load_ex = self.load_ex(objects)
        lt_load_ex = [obj for obj in objects if obj.get_time() <= load_ex]
        get_load_ex = [obj for obj in objects if obj.get_time() > load_ex]
        return self.sorted_descending(lt_load_ex) + self.sorted_ascending(get_load_ex)

    def small_objects(self, objects: set):
        """ First find the smallest object that, if migrated away along with all
            smaller objects, could bring this rank's load below the target load.
            Sort largest to smallest if <= load_ex
            Sort smallest to largest if > load_ex
        """
        load_ex = self.load_ex(objects)
        sorted_objects = self.sorted_ascending(objects)
        accumulated_times = list(accumulate(obj.get_time() for obj in sorted_objects))
        idx = bisect(accumulated_times, load_ex) + 1
        return self.sorted_descending(sorted_objects[:idx]) + self.sorted_ascending(sorted_objects[idx:])

    def largest_objects(self, objects: set):
        """ Objects ordered by object load/time. From bigger to smaller. """
        return self.sorted_descending(objects)
