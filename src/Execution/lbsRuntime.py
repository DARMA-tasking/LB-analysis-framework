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
from logging import Logger
from bisect import bisect
from itertools import accumulate
import math
import sys
from typing import Union
import random

from src.Model.lbsWorkModelBase import WorkModelBase
from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsPhase import Phase
from src.IO.lbsStatistics import compute_function_statistics, inverse_transform_sample, print_function_statistics


class Runtime:
    """A class to handle the execution of the LBS
    """

    def __init__(self, p, w: dict, c: dict, order_strategy: str, logger: Logger = None):
        """Class constructor:
        p: phase instance
        w: dictionary with work model name and optional parameters
        c: dictionary with riterion name and optional parameters
        order_strategy: objects order strategy
        """

        # Assign logger to instance variable
        self.lgr = logger

        # If no LBS phase was provided, do not do anything
        if not isinstance(p, Phase):
            self.lgr.warning("Could not create a LBS runtime without a phase")
            return
        else:
            self.phase = p

        # Instantiate work model
        self.work_model = WorkModelBase.factory(
            w.get("name"), w.get("parameters", {}), lgr=self.lgr)
        if not self.work_model:
            self.lgr.error(f"Could not instantiate a work model of type {self.work_model}")
            sys.exit(1)

        # Transfer critertion type and parameters
        self.criterion_name = c.get("name")
        self.criterion_params = c.get("parameters", {})

        # Initialize load, sent, and work distributions
        self.load_distributions = [[
            p.get_load() for p in self.phase.ranks]]
        self.sent_distributions = [{
            k: v for k, v in self.phase.get_edges().items()}]
        self.work_distributions = [[
            self.work_model.compute(p) for p in self.phase.ranks]]

        # Compute global load, volume and work statistics
        _, l_min, self.average_load, l_max, l_var, _, _, l_imb = compute_function_statistics(
            self.phase.ranks,
            lambda x: x.get_load())
        n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
            self.phase.get_edges().values(),
            lambda x: x)
        n_w, w_min, w_ave, w_max, w_var, _, _, w_imb = compute_function_statistics(
            self.phase.ranks,
            lambda x: self.work_model.compute(x))

        # Initialize run statistics
        self.statistics = {
            "minimum load": [l_min],
            "maximum load": [l_max],
            "load variance": [l_var],
            "load imbalance": [l_imb],
            "number of communication edges": [n_v],
            "maximum largest directed volume": [v_max],
            "total largest directed volume": [n_v * v_ave],
            "minimum work": [w_min],
            "maximum work": [w_max],
            "total work": [n_w * w_ave],
            "work variance": [w_var],
            "work imbalance": [w_imb]}

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
        self.lgr.info(f"Initializing information messages with fanout = {f}")
        gossip_round = 1
        gossips = {}

        # Iterate over all ranks
        for p_snd in rank_set:
            # Reset load information known by sender
            p_snd.reset_all_load_information()

            # Collect message when destination list is not empty
            dst, msg = p_snd.initialize_message(rank_set, f)
            for p_rcv in dst:
                gossips.setdefault(p_rcv, []).append(msg)

        # Process all messages of first round
        for p_rcv, msg_lst in gossips.items():
            for m in msg_lst:
                p_rcv.process_message(m)

        # Report on gossiping status when requested
        for p in rank_set:
            self.lgr.debug(f"\tinformation known to rank {p.get_id()}: {[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Forward messages for as long as necessary and requested
        while gossip_round < n_rounds:
            # Initiate next gossiping round
            self.lgr.info(f"Performing message forwarding round {gossip_round}")
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
                    p_rcv.process_message(m)

            # Report on gossiping status when requested
            for p in rank_set:
                self.lgr.debug(f"\tinformation known to rank {p.get_id()}: "
                               f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Build reverse lookup of ranks to those aware of them
        for p in rank_set:
            # Skip non-loaded ranks
            if not p.get_load():
                continue

            # Update viewers on loaded ranks known to this one
            p.add_as_viewer(p.get_known_loads().keys())

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
            self.lgr.debug(f"\tviewers of rank {p.get_id()}: {[p_o.get_id() for p_o in viewers]}")

        # Report viewers counts to loaded ranks
        n_u, v_min, v_ave, v_max, _, _, _, _ = compute_function_statistics(viewers_counts.values(), lambda x: x)
        self.lgr.info(f"Reporting viewers counts (min:{v_min}, mean: {v_ave:.3g} max: {v_max}) to {n_u} loaded ranks")

    def recursive_extended_search(self, pick_list, object_list, c_fct, n_o, max_n_o):
        """Recursively extend search to other objects
        """

        # Terminate negatively when pick list is empty or maximum depth is reached
        if not pick_list or n_o >= max_n_o:
            return False, n_o

        # Pick one object and move it from one list to the other
        o = random.choice(pick_list)
        pick_list.remove(o)
        object_list.append(o)
        n_o += 1

        # Decide whether criterion allows transfer
        if c_fct(object_list) < 0.:
            # Transfer is not possible, recurse further
            print("   ", c_fct(object_list), "must recurse at level", n_o)
            return self.recursive_extended_search(
                pick_list,
                object_list,
                c_fct,
                n_o,
                max_n_o)
        else:
            # Terminate positively when criterion is satisfied
            print("   terminate positively at level", n_o)
            return True, n_o

        # If this point was reach this is an error
        self.lgr.error("Recursion error at depth". n_o)
        sys.exit(1)

    def transfer_stage(self, transfer_criterion, max_n_objects, deterministic_transfer):
        """Perform object transfer phase
        """

        # Initialize transfer stage
        self.lgr.info("Executing transfer phase")
        n_ignored, n_transfers, n_rejects = 0, 0, 0

        # Iterate over ranks
        for p_src in self.phase.get_ranks():
            # Skip workless ranks
            if not self.work_model.compute(p_src) > 0.:
                continue

            # Skip ranks unaware of peers
            targets = p_src.get_known_loads()
            del targets[p_src]
            if not targets:
                n_ignored += 1
                continue
            self.lgr.debug(f"\ttrying to offload from rank {p_src.get_id()} to {[p.get_id() for p in targets]}:")

            # Offload objects for as long as necessary and possible

            srt_proc_obj = list(self.order_strategy(p_src.migratable_objects))
            while srt_proc_obj:
                # Pick next object in ordered list
                o = srt_proc_obj.pop()
                self.lgr.debug(f"\t* object {o.get_id()}:")

                # Initialize destination information
                p_dst = None
                c_dst = -math.inf

                # Use deterministic or probabilistic transfer method
                if deterministic_transfer:
                    # Select best destination with respect to criterion
                    for p in targets.keys():
                        c = transfer_criterion.compute([o], p_src, p)
                        if c > c_dst:
                            c_dst = c
                            p_dst = p

                else:
                    # Compute transfer CMF given information known to source
                    p_cmf, c_values = p_src.compute_transfer_cmf(
                        transfer_criterion, o, targets, False)
                    self.lgr.debug(f"\t  CMF = {p_cmf}")
                    if not p_cmf:
                        n_rejects += 1
                        continue

                    # Pseudo-randomly select destination proc
                    p_dst = inverse_transform_sample(p_cmf)
                    c_dst = c_values[p_dst]

                # Look for possible transfer including current object
                object_list = [o]
                pick_list = srt_proc_obj[:]
                if c_dst < 0.:
                    # Recursively extend search
                    success, _ = self.recursive_extended_search(
                        pick_list,
                        object_list,
                        lambda x: transfer_criterion.compute(x, p_src, p_dst),
                        1,
                        max_n_objects)
                    if success:
                        # Remove accepted objects from remaining object list
                        srt_proc_obj = pick_list
                    else:
                        # No transferrable list of objects was foumd
                        n_rejects += 1
                        continue

                # Sanity check before transfer
                if p_dst not in p_src.known_loads:
                    self.lgr.error(f"Destination rank {p_dst.get_id()} not in known ranks")

                    sys.exit(1)

                # Transfer objects
                for o in object_list:
                    self.lgr.debug(
                        f"\t\ttransferring object {o.get_id()} ({o.get_time()}) to rank {p_dst.get_id()} "
                        f"(criterion: {c_dst})")
                    p_src.remove_migratable_object(o, p_dst)
                    p_dst.add_migratable_object(o)
                    o.set_rank_id(p_dst.get_id())
                    n_transfers += 1

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects

    def execute(self, n_iterations, n_rounds, f, max_n_objects, deterministic_transfer):
        """Launch runtime execution
        n_iterations: integer number of load-balancing iterations
        n_rounds: integer number of gossiping rounds
        f: integer fanout
        max_n_objects: maxium number of objects transferred at once
        deterministic_transfer: deterministic or probabilistic transfer
        """

        # Compute and report rank work statistics
        print_function_statistics(
            self.phase.get_ranks(),
            lambda x: self.work_model.compute(x), "initial rank works",
            logger=self.lgr)

        # Perform requested number of load-balancing iterations
        for i in range(n_iterations):
            self.lgr.info(f"Starting iteration {i + 1}")

            # Start with information stage
            self.information_stage(n_rounds, f)

            # Instantiate object transfer criterion
            transfer_criterion = CriterionBase.factory(
                self.criterion_name, self.work_model,
                self.criterion_params,
                lgr=self.lgr)
            if not transfer_criterion:
                self.lgr.error(f"Could not instantiate a transfer criterion of type {self.criterion_name}")
                sys.exit(1)

            # Use criterion to perform transfer stage
            n_ignored, n_transfers, n_rejects = self.transfer_stage(
                transfer_criterion,
                max_n_objects,
                deterministic_transfer)

            # Invalidate cache of edges
            self.phase.invalidate_edge_cache()

            # Report iteration statistics
            self.lgr.info(f"Iteration complete ({n_ignored} skipped ranks)")
            n_proposed = n_transfers + n_rejects
            if n_proposed:
                self.lgr.info(f"{n_proposed} proposed transfers, {n_transfers} occurred, {n_rejects} rejected "
                              f"({100. * n_rejects / n_proposed:.4}%)")
            else:
                self.lgr.info("No transfers were proposed")

            # Append new load and sent distributions to existing lists
            self.load_distributions.append([
                p.get_load() for p in self.phase.get_ranks()])
            self.sent_distributions.append({
                k: v for k, v in self.phase.get_edges().items()})
            self.work_distributions.append([
                self.work_model.compute(p) for p in self.phase.ranks])

            # Compute and store global rank load and link volume statistics
            _, l_min, self.load_average, l_max, l_var, _, _, l_imb = compute_function_statistics(
                self.phase.ranks,
                lambda x: x.get_load())
            n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
                self.phase.get_edges().values(),
                lambda x: x)
            n_w, w_min, w_ave, w_max, w_var, _, _, w_imb = compute_function_statistics(
                self.phase.ranks,
                lambda x: self.work_model.compute(x))

            # Update run statistics
            self.statistics["minimum load"].append(l_min)
            self.statistics["maximum load"].append(l_max)
            self.statistics["load variance"].append(l_var)
            self.statistics["load imbalance"].append(l_imb)
            self.statistics["number of communication edges"].append(n_v)
            self.statistics["maximum largest directed volume"].append(v_max)
            self.statistics["total largest directed volume"].append(n_v * v_ave)
            self.statistics["minimum work"].append(w_min)
            self.statistics["maximum work"].append(w_max)
            self.statistics["total work"].append(n_w * w_ave)
            self.statistics["work variance"].append(w_var)
            self.statistics["work imbalance"].append(w_imb)

            # Report partial statistics
            iteration = i + 1
            self.lgr.info(f"Load imbalance({iteration}) = {l_imb:.6g}; min={l_min:.6g}, max={l_max:.6g}, "
                          f"ave={self.load_average:.6g}, std={math.sqrt(l_var):.6g}")

        # Report final mapping when requested
        for p in self.phase.get_ranks():
            self.lgr.debug(f"Rank {p.get_id()}:")
            for o in p.get_objects():
                comm = o.get_communicator()
                if comm:
                    self.lgr.debug(f"  Object {o.get_id()}:")
                    recv = comm.get_received().items()
                    if recv:
                        self.lgr.debug("    received from:")
                        for k, v in recv:
                            self.lgr.debug(f"\tobject {k.get_id()} on rank {k.get_rank_id()}: {v}")
                    sent = comm.get_sent().items()
                    if sent:
                        self.lgr.debug("    sent to:")
                        for k, v in sent:
                            self.lgr.debug(f"\tobject {k.get_id()} on rank {k.get_rank_id()}: {v}")

    @staticmethod
    def sort(objects: set, key):
        return sorted(list(objects), key=key)

    def sorted_ascending(self, objects: Union[set, list]):
        return self.sort(objects, key=lambda x: x.get_time())

    def sorted_descending(self, objects: Union[set, list]):
        return self.sort(objects, key=lambda x: -x.get_time())

    @staticmethod
    def arbitrary(objects: set):
        """ Random strategy: objects are passed without any order
        """

        return objects

    def element_id(self, objects: set):
        """ Order objects by ID
        """

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
