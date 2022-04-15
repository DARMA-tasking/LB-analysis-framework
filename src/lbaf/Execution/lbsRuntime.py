from logging import Logger
from bisect import bisect
from itertools import accumulate
import math
import sys
from typing import Union
import random

from .lbsCriterionBase import CriterionBase
from ..Model.lbsPhase import Phase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsWorkModelBase import WorkModelBase
from ..IO.lbsStatistics import compute_function_statistics, inverse_transform_sample, print_function_statistics, \
    min_Hamming_distance


class Runtime:
    """ A class to handle the execution of the LBS
    """
    def __init__(self, p: Phase, w: dict, c: dict, o_s: str, a: list, brute_force_optimization: bool,
                 logger: Logger = None):
        """ Class constructor:
            p: phase instance
            w: dictionary with work model name and optional parameters
            c: dictionary with criterion name and optional parameters
            o_s: name of object ordering strategy
            a: arrangements that minimize maximum work
            logger: logger for output messages
        """
        # Keep track of list of arrangements with minimax work
        self.__a_min_max = a

        # Assign logger to instance variable
        self.__logger = logger

        # Assign brute_force_optimization to instance variable
        self.bfo = brute_force_optimization

        # If no LBS phase was provided, do not do anything
        if not isinstance(p, Phase):
            self.__logger.warning("Could not create a LBS runtime without a phase")
            return
        else:
            self.__phase = p

        # Instantiate work model
        self.__work_model = WorkModelBase.factory(w.get("name"), w.get("parameters", {}), lgr=self.__logger)
        if not self.__work_model:
            self.__logger.error(f"Could not instantiate a work model of type {self.__work_model}")
            sys.exit(1)

        # Transfer criterion type and parameters
        self.__criterion_name = c.get("name")
        self.__criterion_params = c.get("parameters", {})

        # Initialize load, sent, and work distributions
        self.load_distributions = [[p.get_load() for p in self.__phase.get_ranks()]]
        self.sent_distributions = [{k: v for k, v in self.__phase.get_edges().items()}]
        self.work_distributions = [[self.__work_model.compute(p) for p in self.__phase.get_ranks()]]

        # Compute global load, volume and work statistics
        _, l_min, self.average_load, l_max, l_var, _, _, l_imb = compute_function_statistics(
            self.__phase.get_ranks(),
            lambda x: x.get_load())
        n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
            self.__phase.get_edges().values(),
            lambda x: x)
        n_w, w_min, w_ave, w_max, w_var, _, _, _ = compute_function_statistics(
            self.__phase.get_ranks(),
            lambda x: self.__work_model.compute(x))

        # Compute initial arrangement and report minimum Hamming distance
        arrangement = tuple(
            v for _, v in sorted({
                o.get_id(): p.get_id()
                for p in self.__phase.get_ranks() for o in p.get_objects()
                }.items()))
        hd_min = min_Hamming_distance(arrangement, self.__a_min_max)
        if self.bfo:
            self.__logger.info(f"Iteration 0 minimum Hamming distance to optimal arrangements: {hd_min}")
        self.__logger.debug(f"Iteration 0 arrangement: {arrangement}")

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
            "minimum Hamming distance to optimum": [hd_min]}

        # Initialize strategy
        self.__strategy_mapped = {
            "arbitrary": self.arbitrary,
            "element_id": self.element_id,
            "decreasing_times": self.decreasing_times,
            "increasing_times": self.increasing_times,
            "increasing_connectivity": self.increasing_connectivity,
            "fewest_migrations": self.fewest_migrations,
            "small_objects": self.small_objects}
        if o_s not in self.__strategy_mapped:
            self.__logger.error(f"{o_s} does not exist in known strategies: {[x for x in self.__strategy_mapped.keys()]}")
            sys.exit(1)
        self.__order_strategy = self.__strategy_mapped[o_s]

    def information_stage(self, n_rounds, f):
        """ Execute information phase
            n_rounds: integer number of gossiping rounds
            f: integer fanout
        """
        # Build set of all ranks in the phase
        rank_set = set(self.__phase.get_ranks())

        # Initialize gossip process
        self.__logger.info(f"Initializing information messages with fanout = {f}")
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
            self.__logger.debug(f"information known to rank {p.get_id()}: {[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Forward messages for as long as necessary and requested
        while gossip_round < n_rounds:
            # Initiate next gossiping round
            self.__logger.debug(f"Performing message forwarding round {gossip_round}")
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
                self.__logger.debug(f"information known to rank {p.get_id()}: "
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
            self.__logger.debug(f"viewers of rank {p.get_id()}: {[p_o.get_id() for p_o in viewers]}")

        # Report viewers counts to loaded ranks
        self.__logger.info(f"Completed {n_rounds} information rounds")
        n_v, v_min, v_ave, v_max, _, _, _, _ = compute_function_statistics(viewers_counts.values(), lambda x: x)
        self.__logger.info(f"Reporting viewers counts (min:{v_min}, mean: {v_ave:.3g} max: {v_max}) to {n_v} loaded ranks")

    def recursive_extended_search(self, pick_list, object_list, c_fct, n_o, max_n_o):
        """ Recursively extend search to other objects
        """
        # Fail when no more objects available or maximum depth is reached
        if not pick_list or n_o >= max_n_o:
            return False

        # Pick one object and move it from one list to the other
        o = random.choice(pick_list)
        pick_list.remove(o)
        object_list.append(o)
        n_o += 1

        # Decide whether criterion allows for transfer
        if c_fct(object_list) < 0.:
            # Transfer is not possible, recurse further
            return self.recursive_extended_search(pick_list, object_list, c_fct, n_o, max_n_o)
        else:
            # Succeed when criterion is satisfied
            return True

    def transfer_stage(self, transfer_criterion, max_n_objects, deterministic_transfer):
        """ Perform object transfer phase
        """
        # Initialize transfer stage
        self.__logger.info("Executing transfer phase")
        n_ignored, n_transfers, n_rejects = 0, 0, 0

        # Biggest transfer (num of object transferred at once)
        max_obj_transfers = 0

        # Iterate over ranks
        for p_src in self.__phase.get_ranks():
            # Skip workless ranks
            if not self.__work_model.compute(p_src) > 0.:
                continue

            # Skip ranks unaware of peers
            targets = p_src.get_known_loads()
            del targets[p_src]
            if not targets:
                n_ignored += 1
                continue
            self.__logger.debug(f"trying to offload from rank {p_src.get_id()} to {[p.get_id() for p in targets]}:")

            # Offload objects for as long as necessary and possible
            srt_proc_obj = list(self.__order_strategy(p_src.get_migratable_objects(), p_src.get_id()))
            while srt_proc_obj:
                # Pick next object in ordered list
                o = srt_proc_obj.pop()
                object_list = [o]
                self.__logger.debug(f"* object {o.get_id()}:")

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
                    self.__logger.debug(f"CMF = {p_cmf}")
                    if not p_cmf:
                        n_rejects += 1
                        continue

                    # Pseudo-randomly select destination proc
                    p_dst = inverse_transform_sample(p_cmf)
                    c_dst = c_values[p_dst]

                # Handle case where object not suitable for transfer
                if c_dst < 0.:
                    if not srt_proc_obj:
                        # No more transferable objects are available
                        n_rejects += 1
                        continue

                    # Recursively extend search if possible
                    pick_list = srt_proc_obj[:]
                    success = self.recursive_extended_search(
                        pick_list,
                        object_list,
                        lambda x: transfer_criterion.compute(x, p_src, p_dst),
                        1,
                        max_n_objects)
                    if success:
                        # Remove accepted objects from remaining object list
                        srt_proc_obj = pick_list
                    else:
                        # No transferable list of objects was found
                        n_rejects += 1
                        continue
                    
                # Sanity check before transfer
                if p_dst not in p_src.get_known_loads():
                    self.__logger.error(f"Destination rank {p_dst.get_id()} not in known ranks")
                    sys.exit(1)

                # Transfer objects
                if len(object_list) > max_obj_transfers:
                    max_obj_transfers = len(object_list)

                self.__logger.debug(f"Transferring {len(object_list)} object(s) at once")
                for o in object_list:
                    self.__logger.debug(
                        f"transferring object {o.get_id()} ({o.get_time()}) to rank {p_dst.get_id()} "
                        f"(criterion: {c_dst})")
                    p_src.remove_migratable_object(o, p_dst)
                    p_dst.add_migratable_object(o)
                    o.set_rank_id(p_dst.get_id())
                    n_transfers += 1

        self.__logger.info(f"Maximum number of objects transferred at once: {max_obj_transfers}")

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects

    def execute(self, n_iterations, n_rounds, f, max_n_objects, deterministic_transfer):
        """ Launch runtime execution
            n_iterations: integer number of load-balancing iterations
            n_rounds: integer number of gossiping rounds
            f: integer fanout
            max_n_objects: maximum number of objects transferred at once
            deterministic_transfer: deterministic or probabilistic transfer
        """
        # Report on initial per-rank work
        print_function_statistics(self.__phase.get_ranks(), lambda x: self.__work_model.compute(x), "initial rank works",
                                  logger=self.__logger)

        # Perform requested number of load-balancing iterations
        for i in range(n_iterations):
            self.__logger.info(f"Starting iteration {i + 1}")

            # Start with information stage
            self.information_stage(n_rounds, f)

            # Instantiate object transfer criterion
            transfer_criterion = CriterionBase.factory(self.__criterion_name, self.__work_model, self.__criterion_params,
                                                       lgr=self.__logger)
            if not transfer_criterion:
                self.__logger.error(f"Could not instantiate a transfer criterion of type {self.__criterion_name}")
                sys.exit(1)

            # Use criterion to perform transfer stage
            n_ignored, n_transfers, n_rejects = self.transfer_stage(
                transfer_criterion,
                max_n_objects,
                deterministic_transfer)
            n_proposed = n_transfers + n_rejects
            if n_proposed:
                self.__logger.info(f"{n_proposed} proposed transfers, {n_transfers} occurred, {n_rejects} rejected "
                                f"({100. * n_rejects / n_proposed:.4}%)")
            else:
                self.__logger.info("No transfers were proposed")

            # Invalidate cache of edges
            self.__phase.invalidate_edge_cache()

            # Report iteration statistics
            self.__logger.info(f"Iteration complete ({n_ignored} skipped ranks)")

            # Append new load and sent distributions to existing lists
            self.load_distributions.append([p.get_load() for p in self.__phase.get_ranks()])
            self.sent_distributions.append({k: v for k, v in self.__phase.get_edges().items()})
            self.work_distributions.append([self.__work_model.compute(p) for p in self.__phase.get_ranks()])

            # Compute and store global rank load and link volume statistics
            _, l_min, _, l_max, l_var, _, _, l_imb = compute_function_statistics(
                self.__phase.get_ranks(),
                lambda x: x.get_load())
            n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
                self.__phase.get_edges().values(),
                lambda x: x)
            n_w, w_min, w_ave, w_max, w_var, _, _, _ = print_function_statistics(
                self.__phase.get_ranks(),
                lambda x: self.__work_model.compute(x),
                f"iteration {i + 1} rank works",
                logger=self.__logger)

            # Compute current arrangement and report minimum Hamming distance
            arrangement = tuple(
                v for _, v in sorted({o.get_id(): p.get_id() for p in self.__phase.get_ranks() for o
                                      in p.get_objects()}.items()))
            hd_min = min_Hamming_distance(arrangement, self.__a_min_max)
            if self.bfo:
                self.__logger.info(f"Iteration {i + 1} minimum Hamming distance to optimal arrangements: {hd_min}")
            self.__logger.debug(f"Iteration {i + 1} arrangement: {arrangement}")

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
            self.statistics["minimum Hamming distance to optimum"].append(hd_min)

        # Report final mapping
        for p in self.__phase.get_ranks():
            self.__logger.debug(f"Rank {p.get_id()}:")
            for o in p.get_objects():
                comm = o.get_communicator()
                if comm:
                    self.__logger.debug(f"Object {o.get_id()}:")
                    recv = comm.get_received().items()
                    if recv:
                        self.__logger.debug("received from:")
                        for k, v in recv:
                            self.__logger.debug(f"object {k.get_id()} on rank {k.get_rank_id()}: {v}")
                    sent = comm.get_sent().items()
                    if sent:
                        self.__logger.debug("sent to:")
                        for k, v in sent:
                            self.__logger.debug(f"object {k.get_id()} on rank {k.get_rank_id()}: {v}")

    @staticmethod
    def arbitrary(objects: set, _):
        """ Default: objects are passed as they are stored
        """
        return objects

    @staticmethod
    def element_id(objects: set, _):
        """ Order objects by ID
        """
        return sorted(objects, key=lambda x: x.get_id())

    @staticmethod
    def decreasing_times(objects: set, _):
        """ Order objects by decreasing object times
        """
        return sorted(objects, key=lambda x: -x.get_time())

    @staticmethod
    def increasing_times(objects: set, _):
        """ Order objects by increasing object times
        """
        return sorted(objects, key=lambda x: x.get_time())

    @staticmethod
    def increasing_connectivity(objects: set, src_id):
        """ Order objects by increasing local communication volume
        """
        # Initialize list with all objects without a communicator
        no_comm = [o for o in objects if not isinstance(o.get_communicator(), ObjectCommunicator)]

        # Order objects with a communicator
        with_comm = {}
        for o in objects:
            # Skip objects without a communicator
            comm = o.get_communicator()
            if not isinstance(o.get_communicator(), ObjectCommunicator):
                continue
            
            # Update dict of objects with maximum local communication
            with_comm[o] = max(sum([v for k, v in comm.get_received().items() if k.get_rank_id() == src_id]),
                               sum([v for k, v in comm.get_sent().items() if k.get_rank_id() == src_id]))

        # Return list of objects order by increased local connectivity
        return no_comm + sorted(with_comm, key=with_comm.get)

    @staticmethod
    def sorted_ascending(objects: Union[set, list]):
        return sorted(objects, key=lambda x: x.get_time())

    @staticmethod
    def sorted_descending(objects: Union[set, list]):
        return sorted(objects, key=lambda x: -x.get_time())

    def load_excess(self, objects: set):
        proc_load = sum([obj.get_time() for obj in objects])
        return proc_load - self.average_load

    def fewest_migrations(self, objects: set, _):
        """ First find the load of the smallest single object that, if migrated
            away, could bring this rank's load below the target load.
            Sort largest to the smallest if <= load_excess
            Sort smallest to the largest if > load_excess
        """
        load_excess = self.load_excess(objects)
        lt_load_excess = [obj for obj in objects if obj.get_time() <= load_excess]
        get_load_excess = [obj for obj in objects if obj.get_time() > load_excess]
        return self.sorted_descending(lt_load_excess) + self.sorted_ascending(get_load_excess)

    def small_objects(self, objects: set, _):
        """ First find the smallest object that, if migrated away along with all
            smaller objects, could bring this rank's load below the target load.
            Sort largest to the smallest if <= load_excess
            Sort smallest to the largest if > load_excess
        """
        load_excess = self.load_excess(objects)
        sorted_objects = self.sorted_ascending(objects)
        accumulated_times = list(accumulate(obj.get_time() for obj in sorted_objects))
        idx = bisect(accumulated_times, load_excess) + 1
        return self.sorted_descending(sorted_objects[:idx]) + self.sorted_ascending(sorted_objects[idx:])