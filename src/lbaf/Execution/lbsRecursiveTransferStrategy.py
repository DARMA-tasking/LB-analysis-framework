import sys
import math
import random
from logging import Logger
from typing import Union
from itertools import accumulate
from bisect import bisect

from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsPhase import Phase
from ..Utils.exception_handler import exc_handler
from ..IO.lbsStatistics import inverse_transform_sample
from ..Model.lbsObjectCommunicator import ObjectCommunicator

class RecursiveTransferStrategy(TransferStrategyBase):
    """A concrete class for the recursive transfer strategy."""

    def __init__(self, criterion, parameters: dict, lgr: Logger):
        """Class constructor.

        :param criterion: a CriterionBase instance
        :param parameters: a dictionary of parameters.
        """
        # Call superclass init
        super(RecursiveTransferStrategy, self).__init__(criterion, parameters, lgr)

        # Useful fields
        self.__average_load = None

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
                                f"{[x for x in self.__strategy_mapped]}")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__order_strategy = self.__strategy_mapped[o_s]
        self._logger.info(f"Selected {self.__order_strategy.__name__} object ordering strategy")

    def __recursive_extended_search(self, pick_list, objects, c_fct, n_o, max_n_o):
        """Recursively extend search to other objects."""

        # Fail when no more objects available or maximum depth is reached
        if not pick_list or n_o >= max_n_o:
            return False

        # Pick one object and move it from one list to the other
        o = random.choice(pick_list)
        pick_list.remove(o)
        objects.append(o)
        n_o += 1

        # Decide whether criterion allows for transfer
        if c_fct(objects) < 0.0:
            # Transfer is not possible, recurse further
            return self.__recursive_extended_search(
                pick_list, objects, c_fct, n_o, max_n_o)
        else:
            # Succeed when criterion is satisfied
            return True

    def execute(self, phase: Phase, ave_load: float):
        """Perform object transfer stage."""
        # Initialize transfer stage
        self.__average_load = ave_load
        self._logger.info(f"Executing transfer phase with average load of {self.__average_load}")
        n_ignored, n_transfers, n_rejects, max_obj_transfers = 0, 0, 0, 0

        # Iterate over ranks
        for r_src in phase.get_ranks():
            # Retrieve potential targets
            targets = r_src.get_targets()
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
                o_src = [o]
                self._logger.debug(f"* object {o.get_id()}:")

                # Initialize destination information
                r_dst = None
                c_dst = -math.inf

                # Use deterministic or probabilistic transfer method
                if self._deterministic_transfer:
                    # Select best destination with respect to criterion
                    for r_try in targets.keys():
                        c_try = self._criterion.compute(
                            r_src, o_src, r_try)
                        if c_try > c_dst:
                            c_dst = c_try
                            r_dst = r_try
                else:
                    # Compute transfer CMF given information known to source
                    p_cmf, c_values = r_src.compute_transfer_cmf(
                        self._criterion, o_src, targets, False)
                    self._logger.debug(f"CMF = {p_cmf}")
                    if not p_cmf:
                        n_rejects += 1
                        continue

                    # Pseudo-randomly select destination proc
                    r_dst = inverse_transform_sample(p_cmf)
                    c_dst = c_values[r_dst]

                # Handle case where object not suitable for transfer
                if c_dst < 0.0:
                    # Give up if no objects left of no rank is feasible
                    if not srt_rank_obj or not r_dst:
                        n_rejects += 1
                        continue

                    # Recursively extend search if possible
                    pick_list = srt_rank_obj[:]
                    success = self.__recursive_extended_search(
                        pick_list,
                        o_src,
                        lambda x, r_src=r_src, r_dst=r_dst: self._criterion.compute(r_src, x, r_dst),
                        1,
                        self._max_objects_per_transfer)
                    if success:
                        # Remove accepted objects from remaining object list
                        srt_rank_obj = pick_list
                    else:
                        # No transferable list of objects was found
                        n_rejects += 1
                        continue

                # Transfer objects
                n_transfers += phase.transfer_objects(r_src, o_src, r_dst)

        self._logger.info(
            f"Maximum number of objects transferred at once: {max_obj_transfers}")

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects

    @staticmethod
    def arbitrary(objects: set, _):
        """Default: objects are passed as they are stored."""

        return objects

    @staticmethod
    def element_id(objects: set, _):
        """Order objects by ID."""
        return sorted(objects, key=lambda x: x.get_id())

    @staticmethod
    def decreasing_loads(objects: set, _):
        """Order objects by decreasing object loads."""
        return sorted(objects, key=lambda x: -x.get_load())

    @staticmethod
    def increasing_loads(objects: set, _):
        """Order objects by increasing object loads."""
        return sorted(objects, key=lambda x: x.get_load())

    @staticmethod
    def increasing_connectivity(objects: set, src_id):
        """Order objects by increasing local communication volume."""
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
        """First find the load of the smallest single object that, if migrated
        away, could bring this rank's load below the target load.

        Sort largest to the smallest if <= load_excess
        Sort smallest to the largest if > load_excess.
        """
        load_excess = self.load_excess(objects)
        lt_load_excess = [obj for obj in objects if obj.get_load() <= load_excess]
        get_load_excess = [obj for obj in objects if obj.get_load() > load_excess]
        return self.sorted_descending(lt_load_excess) + self.sorted_ascending(get_load_excess)

    def small_objects(self, objects: set, _):
        """First find the smallest object that, if migrated away along with all
        smaller objects, could bring this rank's load below the target load.

        Sort largest to the smallest if <= load_excess
        Sort smallest to the largest if > load_excess.
        """

        load_excess = self.load_excess(objects)
        sorted_objects = self.sorted_ascending(objects)
        accumulated_loads = list(accumulate(obj.get_load() for obj in sorted_objects))
        idx = bisect(accumulated_loads, load_excess) + 1
        return self.sorted_descending(sorted_objects[:idx]) + self.sorted_ascending(sorted_objects[idx:])
