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
        obj_clusters = {}
        for o in rank.get_migratable_objects():
            # Retrieve shared block ID and skip object without one
            sb_id = o.get_shared_block_id()
            if sb_id == None:
                continue

            # Add current object to its block ID cluster
            obj_clusters.setdefault(sb_id, []).append(o)

        # Return dict of computed object clusters
        return obj_clusters

    def __find_suitable_subclusters(self, clusters, rank_load, r_tol=0.05):
        """ Find suitable sub-clusters to bring rank closest and above average load."""

        # Build dict of suitable clusters with their load
        suitable_subclusters = {}
        n_inspect = 0
        for k, v in clusters.items():
            # Inspect all non-trivial combinations of objects in cluster
            for c in chain.from_iterable(
                combinations(v, p)
                for p in range(1, max(self._max_objects_per_transfer, len(v)) + 1)):
                n_inspect += 1

                # Reject subclusters overshooting within relative tolerance
                reach_load = rank_load - sum([o.get_load() for o in c])
                if reach_load < (1.0 - r_tol) * self.__average_load:
                    continue

                # Retain suitable subclusters with their respective distance and cluster
                suitable_subclusters[c] = (k, reach_load)

        # Return subclusters and cluster IDs sorted by achievable loads
        self._logger.info(f"Found {len(suitable_subclusters)} suitable subclusters amongst {n_inspect} inspected")
        return sorted(suitable_subclusters.items(), key=lambda x: x[1][1])

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
            obj_clusters = self.__cluster_objects(r_src)
            print(obj_clusters.keys())
            self._logger.info(f"Constructed {len(obj_clusters)} object clusters on rank {r_src.get_id()} with load: {r_src.get_load()}")

            # Iterate over suitable subclusters
            found_cluster = False
            for objects, (cluster_ID, reach_load) in self.__find_suitable_subclusters(
                obj_clusters, r_src.get_load()):
                # Initialize destination information
                r_dst = None
                c_dst = -math.inf
                m_dst = math.inf

                # Use deterministic or probabilistic transfer method
                if self._deterministic_transfer:
                    # Determine destinations sharing cluster_ID
                    dst_shared_ID = []
                    dst_non_shared_ID = []

                    # Select best destination with respect to criterion
                    for r_try in targets.keys():
                        s_try = False
                        for o in r_try.get_objects():
                            if o.get_shared_block_id() == cluster_ID:
                                s_try = True
                                dst_shared_ID.append(r_try)
                                break
                        if not s_try:
                            dst_non_shared_ID.append(r_try)
                    actual_targets = dst_shared_ID if dst_shared_ID else dst_non_shared_ID

                    for r_try in targets.keys():
                    #for r_try in actual_targets:
                        c_try = self._criterion.compute(
                            objects, r_src, r_try)
                        m_try = r_try.get_max_memory_usage()
                        if c_try > c_dst:
                            c_dst = c_try
                            r_dst = r_try
                            m_dst = m_try
                        elif c_try == c_dst and m_try < m_dst:
                            r_dst = r_try
                            m_dst = m_try
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

                # Transfer subcluster and break out if best criterion is positive
                if c_dst > 0.0:
                    n_transfers += self._transfer_objects(
                        phase, objects, r_src, r_dst)
                    self._logger.info(
                        f"\trank {r_src.get_id()}, new load: {r_src.get_load()}")
                    self._logger.info(
                        f"\trank {r_dst.get_id()}, new load: {r_dst.get_load()}")
                    break

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects
