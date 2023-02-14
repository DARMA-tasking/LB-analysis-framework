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

        # Define upper bound o

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
            # Skip loadless ranks
            if not r_src.get_load() > 0.:
                continue

            # Skip ranks unaware of peers
            targets = r_src.get_known_loads()
            del targets[r_src]
            if not targets:
                n_ignored += 1
                continue
            self._logger.debug(f"Trying to offload from rank {r_src.get_id()} to {[p.get_id() for p in targets]}:")

            # Cluster migratiable objects on source rank
            obj_clusters = self.__cluster_objects(r_src)
            src_load = r_src.get_load()
            self._logger.info(f"Constructed {len(obj_clusters)} object clusters on rank {r_src.get_id()} with load: {src_load}")

            # Iterate over suitable subclusters
            used_clusters = set()
            for objects, (cluster_ID, reach_load) in self.__find_suitable_subclusters(
                obj_clusters, r_src.get_load()):
                # Skip clusters which were already used for transfers
                # Update cluster containers
                if cluster_ID in used_clusters:
                    continue

                # Initialize destination information
                r_dst = None
                c_dst = -math.inf
                m_dst = math.inf

                # Use deterministic or probabilistic transfer method
                if self._deterministic_transfer:
                    # Select best destination with respect to criterion
                    for r_try in targets.keys():
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

                # Do not transfer whole cluster if best criterion is negative
                if c_dst < 0.0:
                    continue

                # Sanity check before transfer
                if r_dst not in r_src.get_known_loads():
                    self._logger.error(
                        f"Destination rank {r_dst.get_id()} not in known ranks")
                    sys.excepthook = exc_handler
                    raise SystemExit(1)

                # Transfer objects
                for o in objects:
                    phase.transfer_object(o, r_src, r_dst)
                    n_transfers += 1
                self._logger.info(
                    f"Transferred {len(objects)} object(s) from cluster {cluster_ID} to rank {r_dst.get_id()}:")
                self._logger.info(
                    f"\trank {r_src.get_id()}, new load: {r_src.get_load()}")
                self._logger.info(
                    f"\trank {r_dst.get_id()}, new load: {r_dst.get_load()}")

                # Update cluster containers
                obj_clusters.pop(cluster_ID)
                used_clusters.add(cluster_ID)

        # Return object transfer counts
        return n_ignored, n_transfers, n_rejects

