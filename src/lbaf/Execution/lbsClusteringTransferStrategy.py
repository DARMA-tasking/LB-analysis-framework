import sys
import math
import random
from logging import Logger
from typing import Union
from itertools import accumulate
from bisect import bisect

from .lbsTransferStrategyBase import TransferStrategyBase
from .lbsCriterionBase import CriterionBase
from ..Model.lbsPhase import Phase
from ..Utils.exception_handler import exc_handler
from ..IO.lbsStatistics import inverse_transform_sample


class ClusteringTransferStrategy(TransferStrategyBase):
    """ A concrete class for the clustering-based transfer strategy."""

    def __init__(self, criterion, parameters: dict, lgr: Logger):
        """ Class constructor
            criterion: a CriterionBase instance
            parameters: a dictionary of parameters."""

        # Call superclass init
        super(ClusteringTransferStrategy, self).__init__(criterion, parameters, lgr)

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

    def execute(self, phase: Phase):
        """ Perform object transfer stage."""

        # Initialize transfer stage
        self._logger.info("Executing transfer phase")
        n_ignored, n_transfers, n_rejects = 0, 0, 0

        # Iterate over ranks
        for r_src in phase.get_ranks():
            # Skip workless ranks
            if not self._criterion._work_model.compute(r_src) > 0.:
                continue

            # Skip ranks unaware of peers
            targets = r_src.get_known_loads()
            del targets[r_src]
            if not targets:
                n_ignored += 1
                continue
            self._logger.debug(f"Trying to offload from rank {r_src.get_id()} to {[p.get_id() for p in targets]}:")

            # Cluster migratiable objects by shared block ID when available
            obj_clusters = {}
            for o in r_src.get_migratable_objects():
                # Retrieve shared block ID and skip object without one
                sb_id = o.get_shared_block_id()
                if sb_id == None:
                    continue

                # Add current object to its block ID cluster
                obj_clusters.setdefault(sb_id, []).append(o)

            self._logger.info(f"Constructed {len(obj_clusters)} object clusters on rank {r_src.get_id()}")

            # Iterate over clusters
            remaining_clusters = []
            for cluster_key, objects in obj_clusters.items():
                # Initialize destination information
                r_dst = None
                c_dst = -math.inf

                # Use deterministic or probabilistic transfer method
                if self._deterministic_transfer:
                    # Select best destination with respect to criterion
                    for r_try in targets.keys():
                        c_try = self._criterion.compute(
                            objects, r_src, r_try)
                        if c_try > c_dst:
                            c_dst = c_try
                            r_dst = r_try
                else:
                    # Compute transfer CMF given information known to source
                    p_cmf, c_values = r_src.compute_transfer_cmf(
                        self._criterion, objects, targets, False)
                    self._logger.debug(f"CMF = {p_cmf}")
                    if not p_cmf:
                        n_rejects += 1
                        continue

                    # Pseudo-randomly select destination proc
                    r_dst = inverse_transform_sample(p_cmf)
                    c_dst = c_values[r_dst]

                # Do not transfer whole cluster if best criterion is negative
                if c_dst < 0.0:
                    remaining_clusters.append(cluster_key)
                    continue

                # Sanity check before transfer
                if r_dst not in r_src.get_known_loads():
                    self._logger.error(
                        f"Destination rank {r_dst.get_id()} not in known ranks")
                    sys.excepthook = exc_handler
                    raise SystemExit(1)

                # Transfer objects
                self._logger.info(
                    f"Transferring {len(objects)} object(s) from cluster {cluster_key} to rank {r_dst.get_id()}")
                for o in objects:
                    phase.transfer_object(o, r_src, r_dst)
                    n_transfers += 1

            # Inspect remaining clusters
            for cluster_key in remaining_clusters:
                print("Rank", r_src, "now has load", r_src.get_load())
                self._logger.info(
                    f"Inspecting non-transferred cluster with key {cluster_key}")
                for o in obj_clusters[cluster_key]:
                    print("trying to add", o.get_id())
                    # Select best destination with respect to criterion
                    r_dst = None
                    c_dst = -math.inf
                    for r_try in targets.keys():
                        c_try = self._criterion.compute(
                            [o], r_src, r_try)
                        print(f"\ttrying to send {o.get_id()} to", r_try, "with load", r_try.get_load(), "c=", c_try)
                        if c_try > c_dst:
                            c_dst = c_try
                            r_dst = r_try
                    if c_dst > 0.0:
                        print(f"Transferring {o.get_id()} to", r_dst, c_dst)
                        phase.transfer_object(o, r_src, r_dst)
                        n_transfers += 1

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects

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
