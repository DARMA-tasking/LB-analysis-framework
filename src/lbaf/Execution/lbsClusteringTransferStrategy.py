import sys
import math
import random
from logging import Logger
from typing import Union
from itertools import accumulate, chain, combinations
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

    def __cluster_objects(self, rank):
        """ Cluster migratiable objects by shared block ID when available."""

        # Iterate over all migratable objects on rank
        clusters = {}
        for o in rank.get_migratable_objects():
            # Retrieve shared block ID and skip object without one
            sb_id = o.get_shared_block_id()
            if sb_id == None:
                continue

            # Add current object to its block ID cluster
            clusters.setdefault(sb_id, []).append(o)

        # Return dict of computed object clusters
        return clusters

    def __find_suitable_subclusters(self, clusters, rank_load, r_tol=0.05):
        """ Find suitable sub-clusters to bring rank closest and above average load."""

        # Build dict of suitable clusters with their load
        suitable_subclusters = {}
        n_inspect = 0
        breaks = [False, False]
        for v in clusters.values():
            n_comb = 0
            # Inspect all non-trivial combinations of objects in cluster
            for c in chain.from_iterable(
                combinations(v, p)
                for p in range(1, max(self._max_objects_per_transfer, len(v)) + 1)):
                # Limit number of inspected combinations
                n_comb += 1
                if n_comb > 65535:
                    breaks[0] = True
                    break

                # Reject subclusters overshooting within relative tolerance
                n_inspect += 1
                reach_load = rank_load - sum([o.get_load() for o in c])
                if reach_load < (1.0 - r_tol) * self.__average_load:
                    continue

                # Retain suitable subclusters with their respective distance and cluster
                suitable_subclusters[c] = reach_load

                # Limit number of returned suitable clusters
                if len(suitable_subclusters) > 25:
                    breaks[1] = True
                    break

            # Break out early when one of the limiters was triggered
            if breaks[0] or breaks[1]:
                self._logger.info(
                    f"Breaking out early after {n_comb} combinations inspected")
                break

        # Return subclusters and cluster IDs sorted by achievable loads
        self._logger.info(
            f"Found {len(suitable_subclusters)} suitable subclusters amongst {n_inspect} inspected")
        return sorted(suitable_subclusters.keys(), key=suitable_subclusters.get)

    def execute(self, phase: Phase, ave_load: float):
        """ Perform object transfer stage."""

        # Initialize transfer stage
        self.__average_load = ave_load
        self._logger.info(f"Executing transfer phase with average load: {self.__average_load}")
        n_ignored, n_transfers, n_rejects = 0, 0, 0

        # Iterate over ranks
        for r_src in phase.get_ranks():
            # Retrieve potential targets
            targets = r_src.get_targets()
            if not targets:
                n_ignored += 1
                continue
            self._logger.debug(f"Trying to offload from rank {r_src.get_id()} to {[p.get_id() for p in targets]}:")

            # Cluster migratiable objects on source rank
            clusters_src = self.__cluster_objects(r_src)
            self._logger.info(f"Constructed {len(clusters_src)} object clusters on rank {r_src.get_id()} with load: {r_src.get_load()}")

            # Identify and perform beneficial cluster swaps
            n_swaps = 0
            for o_src in clusters_src.values():
                cluster_load = sum([o.get_load() for o in o_src])
                swapped_cluster = False
                for r_try in targets.keys():
                    # Compute initial load difference
                    l_src, l_try = r_src.get_load(), r_try.get_load()
                    l_max_0 = max(l_src, l_try)
                    for o_try in self.__cluster_objects(r_try).values():
                        # Decide whether swap is beneficial
                        l_o_try = cluster_load - sum([o.get_load() for o in o_try])
                        if l_max_0 > max(
                            l_src - l_o_try, l_try + l_o_try):
                            # Perform swap
                            n_transfers += self._swap_objects(
                                phase, r_src, o_src, r_try, o_try)
                            self._logger.info(
                                f"\trank {r_src.get_id()}, new load: {r_src.get_load()}")
                            self._logger.info(
                                f"\trank {r_try.get_id()}, new load: {r_try.get_load()}")
                            swapped_cluster = True
                            n_swaps += 1
                            break

                    # Break out from targets loop once one swap was performed
                    if swapped_cluster:
                        break

            # Recompute rank cluster when swaps have occurred
            if n_swaps:
                clusters_src = self.__cluster_objects(r_src)
                self._logger.info(
                    f"Performed {n_swaps} cluster swaps from rank {r_src.get_id()}")

            # Iterate over suitable subclusters
            found_cluster = False
            for o_src in self.__find_suitable_subclusters(clusters_src, r_src.get_load()):
                # Initialize destination information
                objects_load = sum([o.get_load() for o in o_src])
                r_dst = None
                c_dst = -math.inf
                l_dst = math.inf

                # Use deterministic or probabilistic transfer method
                if self._deterministic_transfer:
                    for r_try in targets.keys():
                        c_try = self._criterion.compute(
                            r_src, o_src, r_try)
                        if c_try <= 0.0:
                            continue
                        l_try = abs(r_try.get_load() + objects_load - ave_load)
                        if l_try < l_dst:
                            c_dst = c_try
                            l_dst = l_try
                            r_dst = r_try
                        elif l_try == l_dst and c_try > c_dst:
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

                # Transfer subcluster and break out if best criterion is positive
                if c_dst > 0.0:
                    n_transfers += self._transfer_objects(
                        phase, r_src, o_src, r_dst)
                    self._logger.info(
                        f"\trank {r_src.get_id()}, new load: {r_src.get_load()}")
                    self._logger.info(
                        f"\trank {r_dst.get_id()}, new load: {r_dst.get_load()}")
                    break

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects
