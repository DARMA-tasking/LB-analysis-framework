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

from src.Model.lbsWorkModelBase import WorkModelBase
from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsPhase import Phase
from src.IO.lbsStatistics import compute_function_statistics, inverse_transform_sample, print_function_statistics


class Runtime:
    """A class to handle the execution of the LBS
    """

    def __init__(self, p, w: dict, c: dict, order_strategy: str, v=False):
        """Class constructor:
        p: phase instance
        w: dictionary with work model name and optional parameters
        c: dictionary with riterion name and optional parameters
        order_strategy: Objects order strategy
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

        # Instantiate work model
        self.work_model = WorkModelBase.factory(
            w.get("name"),
            w.get("parameters", {}))
        if not self.work_model:
            print(bcolors.ERR
                + "*  ERROR: could not instantiate a work model of tyoe {}".format(self.work_model_name)
                + bcolors.END)
            sys.exit(1)

        # Transfer critertion type and parameters
        self.criterion_name = c.get("name")
        self.criterion_params = c.get("parameters", {})

        # Verbosity of runtime
        self.verbose = v

        # Initialize load, sent, and work distributions
        self.load_distributions = [[
            p.get_load() for p in self.phase.ranks]]
        self.sent_distributions = [{
            k:v for k,v in self.phase.get_edges().items()}]
        self.work_distributions = [[
            self.work_model.compute(p) for p in self.phase.ranks]]

        # Compute global load, volume and work statistics
        _, l_min, self.average_load, l_max, l_var, _, _, l_imb = compute_function_statistics(
            self.phase.ranks,
            lambda x: x.get_load())
        n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
            self.phase.get_edges().values(),
            lambda x: x)
        _, w_min, self.average_work, w_max, w_var, _, _, w_imb = compute_function_statistics(
            self.phase.ranks,
            lambda x: self.work_model.compute(x))

        # Initialize run statistics
        self.statistics = {
            "minimum load"                  : [l_min],
            "maximum load"                  : [l_max],
            "load variance"                 : [l_var],
            "load imbalance"                : [l_imb],
            "number of communication edges" : [n_v],
            "maximum communication volume"  : [v_max],
            "total communication volume": [n_v * v_ave],
            "minimum work"                  : [w_min],
            "maximum work"                  : [w_max],
            "work variance"                 : [w_var],
            "work imbalance"                : [w_imb]}

        # Initialize strategy
        self.strategy_mapped = {
            "arbitrary": self.arbitrary,
            "element_id": self.element_id,
            "fewest_migrations": self.fewest_migrations,
            "small_objects": self.small_objects,
            "largest_objects": self.largest_objects}
        self.order_strategy = self.strategy_mapped.get(order_strategy, None)

    def information_stage(self, n_rounds, f):
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
            + "Initializing information messages with fanout = {}".format(
            f))
        gossip_round = 1
        gossips = {}

        # Iterate over all ranks
        for p_snd in rank_set:
            # Reset load information known by sender
            p_snd.reset_all_load_information()

            # Collect message when destination list is not empty
            dst, msg = p_snd.initialize_works(rank_set, f)
            for p_rcv in dst:
                gossips.setdefault(p_rcv, []).append(msg)

        # Process all messages of first round
        for p_rcv, msg_lst in gossips.items():
            for m in msg_lst:
                p_rcv.process_message(m)

        # Report on gossiping status when requested
        if self.verbose:
            for p in rank_set:
                print("\tloaded known to rank {}: {}".format(
                    p.get_id(),
                    [p_u.get_id() for p_u in p.get_known_ranks()]))

        # Forward messages for as long as necessary and requested
        while gossip_round < n_rounds:
            # Initiate next gossiping roung
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Performing message forwarding round {}".format(
                gossip_round))
            gossip_round += 1
            gossips.clear()

            # Iterate over all ranks
            for p_snd in rank_set:
                # Check whether rank must relay previously received message
                if p_snd.round_last_received + 1 == gossip_round:
                    # Collect message when destination list is not empty
                    dst, msg = p_snd.forward_message(gossip_round, rank_set, f)
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
                        [p_u.get_id() for p_u in p.get_known_ranks()]))

        # Build reverse lookup of loaded to overloaded viewers
        for p in rank_set:
            # Skip non-loaded ranks
            if not p.get_load():
                continue

            # Update viewers on loaded ranks known to this one
            p.add_as_viewer(p.get_known_ranks())

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

    def transfer_stage(self, transfer_criterion):
        """Perform object transfer phase
        """

        # Initialize transfer stage
        print(bcolors.HEADER
            + "[RunTime] "
            + bcolors.END
            + "Excuting transfer phase")
        n_ignored, n_transfers, n_rejects = 0, 0, 0

        # Iterate over ranks
        for p_src in self.phase.get_ranks():
            # Skip workless ranks
            if not self.work_model.compute(p_src) > 0.:
                continue

            # Skip ranks unaware of peers
            works = p_src.get_known_works()
            if not works:
                n_ignored += 1
                continue

            # Offload objects for as long as necessary and possible
            srt_proc_obj = self.order_strategy(p_src.migratable_objects)
            obj_it = iter(srt_proc_obj)
            while works:
                # Pick next object
                try:
                    o = next(obj_it)
                except:
                    # List of objects is exhausted, break out
                    break

                # Compute transfer CMF given known works
                p_cmf = p_src.compute_transfer_cmf()
                if not p_cmf:
                    continue

                # Pseudo-randomly select destination proc
                p_dst = inverse_transform_sample(
                    works.keys(),
                    p_cmf)

                # Report on overloaded rank when requested
                if self.verbose:
                    print("\tknown ranks: {}".format(
                        [u.get_id() for u in works]))
                    print("\tknown works: {}".format(
                        [self.work_model.compute(u) for u in works]))
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

                    # Sanity check before transfer
                    if p_dst not in p_src.known_works:
                        print(bcolors.ERR
                              + "*  ERROR: destination rank {} not in known ranks".format(
                                  p_dst.get_id())
                              + bcolors.END)
                        sys.exit(1)

                    # Transfer object
                    p_src.remove_migratable_object(o, p_dst, self.work_model)
                    obj_it = iter(p_src.get_migratable_objects())
                    p_dst.add_migratable_object(o)
                    n_transfers += 1

                # Update peers known to rank
                works = p_src.get_known_works()

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects

    def execute(self, n_iterations, n_rounds, f):
        """Launch runtime execution
        n_iterations: integer number of load-balancing iterations
        n_rounds: integer number of gossiping rounds
        f: integer fanout
        """

        # Compute and report rank work statistics
        print_function_statistics(self.phase.get_ranks(),
                                  lambda x: self.work_model.compute(x),
                                  "initial rank works",
                                  self.verbose)

        # Perform requested number of load-balancing iterations
        for i in range(n_iterations):
            print(bcolors.HEADER
                + "[RunTime] "
                + bcolors.END
                + "Starting iteration {}".format(
                i + 1))

            # Start with information stage
            self.information_stage(n_rounds, f)

            # Instantiate object transfer criterion
            transfer_criterion = CriterionBase.factory(
                self.criterion_name,
                set(self.phase.get_ranks()),
                self.phase.get_edges(),
                self.criterion_params)
            if not transfer_criterion:
                print(bcolors.ERR
                    + "*  ERROR: could not instantiate a transfer criterion of type {}".format(self.criterion_name)
                    + bcolors.END)
                sys.exit(1)

            # Use criterion to perform transfer stage
            n_ignored, n_transfers, n_rejects = self.transfer_stage(
                transfer_criterion)

             # Invalidate cache of edges
            self.phase.invalidate_edge_cache()

            # Report iteration statistics
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
            self.work_distributions.append([
                self.work_model.compute(p) for p in self.phase.ranks])

            # Compute and store global rank load and link volume statistics
            _, l_min, self.load_average, l_max, l_var, _, _, l_imb = compute_function_statistics(
                self.phase.ranks,
                lambda x: x.get_load())
            n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
                self.phase.get_edges().values(),
                lambda x: x)
            _, w_min, self.average_work, w_max, w_var, _, _, w_imb = compute_function_statistics(
                self.phase.ranks,
                lambda x: self.work_model.compute(x))

            # Update run statistics
            self.statistics["minimum load"].append(l_min)
            self.statistics["maximum load"].append(l_max)
            self.statistics["load variance"].append(l_var)
            self.statistics["load imbalance"].append(l_imb)
            self.statistics["number of communication edges"].append(n_v)
            self.statistics["maximum communication volume"].append(v_max)
            self.statistics["total communication volume"].append(n_v * v_ave)
            self.statistics["minimum work"].append(w_min)
            self.statistics["maximum work"].append(w_max)
            self.statistics["work variance"].append(w_var)
            self.statistics["work imbalance"].append(w_imb)

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

    def load_excess(self, objects: set):
        proc_load = sum([obj.get_time() for obj in objects])
        return proc_load - self.average_load

    def fewest_migrations(self, objects: set):
        """ First find the load of the smallest single object that, if migrated
            away, could bring this rank's load below the target load.
            Sort largest to smallest if <= load_excess
            Sort smallest to largest if > load_excess
        """

        load_excess = self.load_excess(objects)
        lt_load_excess = [obj for obj in objects if obj.get_time() <= load_excess]
        get_load_excess = [obj for obj in objects if obj.get_time() > load_excess]
        return self.sorted_descending(lt_load_excess) + self.sorted_ascending(get_load_excess)

    def small_objects(self, objects: set):
        """ First find the smallest object that, if migrated away along with all
            smaller objects, could bring this rank's load below the target load.
            Sort largest to smallest if <= load_excess
            Sort smallest to largest if > load_excess
        """

        load_excess = self.load_excess(objects)
        sorted_objects = self.sorted_ascending(objects)
        accumulated_times = list(accumulate(obj.get_time() for obj in sorted_objects))
        idx = bisect(accumulated_times, load_excess) + 1
        return self.sorted_descending(sorted_objects[:idx]) + self.sorted_ascending(sorted_objects[idx:])

    def largest_objects(self, objects: set):
        """ Objects ordered by object load/time. From bigger to smaller.
        """

        return self.sorted_descending(objects)
