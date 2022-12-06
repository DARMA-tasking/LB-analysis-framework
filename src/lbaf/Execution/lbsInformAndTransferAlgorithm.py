import sys
import math
import random
from logging import Logger
from typing import Union
from itertools import accumulate
from bisect import bisect

from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import compute_function_statistics, print_function_statistics, inverse_transform_sample, \
    min_Hamming_distance
from ..Utils.exception_handler import exc_handler


class InformAndTransferAlgorithm(AlgorithmBase):
    """ A concrete class for the 2-phase gossip+transfer algorithm."""

    def __init__(self, work_model, parameters: dict, lgr: Logger, qoi_name: str):
        """ Class constructor
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters.
            qoi_name: a quantity of interest."""

        # Call superclass init
        super(InformAndTransferAlgorithm, self).__init__(
            work_model, parameters, lgr, qoi_name)

        # Retrieve mandatory integer parameters
        self.__n_iterations = parameters.get("n_iterations")
        if not isinstance(self.__n_iterations, int) or self.__n_iterations < 0:
            self._logger.error(
                f"Incorrect provided number of algorithm iterations: {self.__n_iterations}")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__n_rounds = parameters.get("n_rounds")
        if not isinstance(self.__n_rounds, int) or self.__n_rounds < 0:
            self._logger.error(
                f"Incorrect provided number of information rounds: {self.__n_rounds}")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__fanout = parameters.get("fanout")
        if not isinstance(self.__fanout, int) or self.__fanout < 0:
            self._logger.error(f"Incorrect provided information fanout {self.__fanout}")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._logger.info(
            f"Instantiated with {self.__n_iterations} iterations, {self.__n_rounds} rounds, fanout {self.__fanout}")

        # Select object order strategy
        self.__strategy_mapped = {
            "arbitrary": self.arbitrary,
            "element_id": self.element_id,
            "decreasing_loads": self.decreasing_loads,
            "increasing_loads": self.increasing_loads,
            "increasing_connectivity": self.increasing_connectivity,
            "fewest_migrations": self.fewest_migrations,
            "small_objects": self.small_objects}
        o_s = parameters.get("order_strategy")
        if o_s not in self.__strategy_mapped:
            self._logger.error(f"{o_s} does not exist in known ordering strategies: "
                                f"{[x for x in self.__strategy_mapped.keys()]}")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__order_strategy = self.__strategy_mapped[o_s]
        self._logger.info(f"Selected {self.__order_strategy.__name__} object ordering strategy")

        # Try to instantiate object transfer criterion
        self.__transfer_criterion = CriterionBase.factory(
            parameters.get("criterion"),
            self.work_model,
            lgr=self._logger)
        if not self.__transfer_criterion:
            self._logger.error(f"Could not instantiate a transfer criterion of type {self.__criterion_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Assign optional parameters
        self.__deterministic_transfer = parameters.get("deterministic_transfer", False)
        self.__max_objects_per_transfer = parameters.get("max_objects_per_transfer", math.inf) 

    def information_stage(self):
        """ Execute information stage."""
        
        # Build set of all ranks in the phase
        rank_set = set(self.phase.get_ranks())

        # Initialize information messages
        self._logger.info(f"Initializing information messages with fanout={self.__fanout}")
        information_round = 1
        messages = {}

        # Iterate over all ranks
        for p_snd in rank_set:
            # Reset load information known by sender
            p_snd.reset_all_load_information()

            # Collect message when destination list is not empty
            dst, msg = p_snd.initialize_message(rank_set, self.__fanout)
            for p_rcv in dst:
                messages.setdefault(p_rcv, []).append(msg)

        # Process all messages of first round
        for p_rcv, msg_lst in messages.items():
            for m in msg_lst:
                p_rcv.process_message(m)

        # Report on gossiping status when requested
        for p in rank_set:
            self._logger.debug(f"information known to rank {p.get_id()}: "
                                f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Forward messages for as long as necessary and requested
        while information_round < self.__n_rounds:
            # Initiate next gossiping round
            self._logger.debug(f"Performing message forwarding round {information_round}")
            information_round += 1
            messages.clear()

            # Iterate over all ranks
            for p_snd in rank_set:
                # Check whether rank must relay previously received message
                if p_snd.round_last_received + 1 == information_round:
                    # Collect message when destination list is not empty
                    dst, msg = p_snd.forward_message(information_round, rank_set, self.__fanout)
                    for p_rcv in dst:
                        messages.setdefault(p_rcv, []).append(msg)

            # Process all messages of first round
            for p_rcv, msg_lst in messages.items():
                for m in msg_lst:
                    p_rcv.process_message(m)

            # Report on gossiping status when requested
            for p in rank_set:
                self._logger.debug(f"information known to rank {p.get_id()}: "
                                    f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Build reverse lookup of ranks to those aware of them
        for p in rank_set:
            # Skip non-loaded ranks
            if not p.get_load():
                continue

    def recursive_extended_search(self, pick_list, object_list, c_fct, n_o, max_n_o):
        """ Recursively extend search to other objects."""
        
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
            return self.recursive_extended_search(
                pick_list, object_list, c_fct, n_o, max_n_o)
        else:
            # Succeed when criterion is satisfied
            return True

    def transfer_stage(self):
        """ Perform object transfer stage."""
        
        # Initialize transfer stage
        self._logger.info("Executing transfer phase")
        n_ignored, n_transfers, n_rejects = 0, 0, 0

        # Biggest transfer (num of object transferred at once)
        max_obj_transfers = 0

        # Iterate over ranks
        for r_src in self.phase.get_ranks():
            # Skip workless ranks
            if not self.work_model.compute(r_src) > 0.:
                continue

            # Skip ranks unaware of peers
            targets = r_src.get_known_loads()
            del targets[r_src]
            if not targets:
                n_ignored += 1
                continue
            self._logger.debug(f"Trying to offload from rank {r_src.get_id()} to {[p.get_id() for p in targets]}:")

            # Offload objects for as long as necessary and possible
            srt_rank_obj = list(self.__order_strategy(
                r_src.get_migratable_objects(), r_src.get_id()))
            while srt_rank_obj:
                # Pick next object in ordered list
                o = srt_rank_obj.pop()
                object_list = [o]
                self._logger.debug(f"* object {o.get_id()}:")

                # Initialize destination information
                r_dst = None
                c_dst = -math.inf

                # Use deterministic or probabilistic transfer method
                if self.__deterministic_transfer:
                    # Select best destination with respect to criterion
                    for p in targets.keys():
                        c = self.__transfer_criterion.compute([o], r_src, p)
                        if c > c_dst:
                            c_dst = c
                            r_dst = p
                else:
                    # Compute transfer CMF given information known to source
                    p_cmf, c_values = r_src.compute_transfer_cmf(
                        self.__transfer_criterion, o, targets, False)
                    self._logger.debug(f"CMF = {p_cmf}")
                    if not p_cmf:
                        n_rejects += 1
                        continue

                    # Pseudo-randomly select destination proc
                    r_dst = inverse_transform_sample(p_cmf)
                    c_dst = c_values[r_dst]

                # Handle case where object not suitable for transfer
                if c_dst < 0.:
                    if not srt_rank_obj:
                        # No more transferable objects are available
                        n_rejects += 1
                        continue

                    # Recursively extend search if possible
                    pick_list = srt_rank_obj[:]
                    success = self.recursive_extended_search(
                        pick_list,
                        object_list,
                        lambda x: self.__transfer_criterion.compute(x, r_src, r_dst),
                        1,
                        self.__max_objects_per_transfer)
                    if success:
                        # Remove accepted objects from remaining object list
                        srt_rank_obj = pick_list
                    else:
                        # No transferable list of objects was found
                        n_rejects += 1
                        continue
                    
                # Sanity check before transfer
                if r_dst not in r_src.get_known_loads():
                    self._logger.error(
                        f"Destination rank {r_dst.get_id()} not in known ranks")
                    sys.excepthook = exc_handler
                    raise SystemExit(1)

                # Transfer objects
                if len(object_list) > max_obj_transfers:
                    max_obj_transfers = len(object_list)

                self._logger.debug(
                    f"Transferring {len(object_list)} object(s) at once")
                for o in object_list:
                    self.phase.transfer_object(o, r_src, r_dst)
                    n_transfers += 1

        self._logger.info(
            f"Maximum number of objects transferred at once: {max_obj_transfers}")

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects

    def execute(self, phases: list, distributions: dict, statistics: dict, a_min_max):
        """ Execute 2-phase gossip+transfer algorithm on Phase instance."""
        
        # Ensure that a list with at least one phase was provided
        if not phases or not isinstance(phases, list) or not isinstance((phase := phases[0]), Phase):
            self._logger.error(f"Algorithm execution requires a Phase instance")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.phase = phase

        # Initialize run distributions and statistics
        self.update_distributions_and_statistics(distributions, statistics)

        # Keep track of average load
        self.__average_load = statistics.get("average load", math.nan)

        # Perform requested number of load-balancing iterations
        for i in range(self.__n_iterations):
            self._logger.info(f"Starting iteration {i + 1}")

            # Start with information stage
            self.information_stage()

            # Then execute transfer stage
            n_ignored, n_transfers, n_rejects = self.transfer_stage()
            n_proposed = n_transfers + n_rejects
            if n_proposed:
                self._logger.info(
                    f"{n_proposed} proposed transfers, {n_transfers} occurred, {n_rejects} rejected "
                    f"({100. * n_rejects / n_proposed:.4}%)")
            else:
                self._logger.info("No transfers were proposed")

            # Report iteration statistics
            self._logger.info(f"Iteration complete ({n_ignored} skipped ranks)")

            # Compute and report iteration work statistics
            n_w, w_min, w_ave, w_max, w_var, _, _, _ = print_function_statistics(
                self.phase.get_ranks(),
                lambda x: self.work_model.compute(x),
                f"iteration {i + 1} rank work",
                self._logger)

            # Update run distributions and statistics
            self.update_distributions_and_statistics(distributions, statistics)

            # Compute current arrangement
            arrangement = tuple(
                v for _, v in sorted(
                    {o.get_id(): p.get_id()
                     for p in self.phase.get_ranks()
                     for o in p.get_objects()}.items()))
            self._logger.debug(f"Iteration {i + 1} arrangement: {arrangement}")

            # Report minimum Hamming distance when minimax optimum is available
            if a_min_max:
                hd_min = min_Hamming_distance(arrangement, a_min_max)
                self._logger.info(
                    f"Iteration {i + 1} minimum Hamming distance to optimal arrangements: {hd_min}")
                statistics["minimum Hamming distance to optimum"].append(hd_min)

        # Report final mapping in debug mode
        self.report_final_mapping(self._logger)

    @staticmethod
    def arbitrary(objects: set, _):
        """ Default: objects are passed as they are stored."""
        
        return objects

    @staticmethod
    def element_id(objects: set, _):
        """ Order objects by ID."""
        
        return sorted(objects, key=lambda x: x.get_id())

    @staticmethod
    def decreasing_loads(objects: set, _):
        """ Order objects by decreasing object loads."""
        
        return sorted(objects, key=lambda x: -x.get_load())

    @staticmethod
    def increasing_loads(objects: set, _):
        """ Order objects by increasing object loads."""
        
        return sorted(objects, key=lambda x: x.get_load())

    @staticmethod
    def increasing_connectivity(objects: set, src_id):
        """ Order objects by increasing local communication volume."""
        
        # Initialize list with all objects without a communicator
        no_comm = [
            o for o in objects
            if not isinstance(o.get_communicator(), ObjectCommunicator)]

        # Order objects with a communicator
        with_comm = {}
        for o in objects:
            # Skip objects without a communicator
            comm = o.get_communicator()
            if not isinstance(o.get_communicator(), ObjectCommunicator):
                continue
            
            # Update dict of objects with maximum local communication
            with_comm[o] = max(
                sum([v for k, v in comm.get_received().items()
                     if k.get_rank_id() == src_id]),
                sum([v for k, v in comm.get_sent().items()
                     if k.get_rank_id() == src_id]))

        # Return list of objects order by increased local connectivity
        return no_comm + sorted(with_comm, key=with_comm.get)

    @staticmethod
    def sorted_ascending(objects: Union[set, list]):
        return sorted(objects, key=lambda x: x.get_load())

    @staticmethod
    def sorted_descending(objects: Union[set, list]):
        return sorted(objects, key=lambda x: -x.get_load())

    def load_excess(self, objects: set):
        rank_load = sum([obj.get_load() for obj in objects])
        return rank_load - self.__average_load

    def fewest_migrations(self, objects: set, _):
        """ First find the load of the smallest single object that, if migrated
            away, could bring this rank's load below the target load.
            Sort largest to the smallest if <= load_excess
            Sort smallest to the largest if > load_excess."""
        
        load_excess = self.load_excess(objects)
        lt_load_excess = [obj for obj in objects if obj.get_load() <= load_excess]
        get_load_excess = [obj for obj in objects if obj.get_load() > load_excess]
        return self.sorted_descending(lt_load_excess) + self.sorted_ascending(get_load_excess)

    def small_objects(self, objects: set, _):
        """ First find the smallest object that, if migrated away along with all
            smaller objects, could bring this rank's load below the target load.
            Sort largest to the smallest if <= load_excess
            Sort smallest to the largest if > load_excess."""
        
        load_excess = self.load_excess(objects)
        sorted_objects = self.sorted_ascending(objects)
        accumulated_loads = list(accumulate(obj.get_load() for obj in sorted_objects))
        idx = bisect(accumulated_loads, load_excess) + 1
        return self.sorted_descending(sorted_objects[:idx]) + self.sorted_ascending(sorted_objects[idx:])
