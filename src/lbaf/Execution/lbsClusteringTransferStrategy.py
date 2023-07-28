import math
import random
from itertools import chain, combinations
from logging import Logger

import numpy.random as nr

from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import inverse_transform_sample


class ClusteringTransferStrategy(TransferStrategyBase):
    """A concrete class for the clustering-based transfer strategy."""

    def __init__(self, criterion, parameters: dict, lgr: Logger):
        """Class constructor.

        :param criterion: a CriterionBase instance.
        :param parameters: a dictionary of parameters.
        :param lgr: a Logger instance.
        """
        # Call superclass init
        super(ClusteringTransferStrategy, self).__init__(criterion, parameters, lgr)

    def __cluster_objects(self, rank):
        """Cluster migratiable objects by shared block ID when available."""
        # Iterate over all migratable objects on rank
        clusters = {}
        for o in rank.get_migratable_objects():
            # Retrieve shared block ID and skip object without one
            sb_id = o.get_shared_block_id()
            if sb_id is None:
                continue

            # Add current object to its block ID cluster
            clusters.setdefault(sb_id, []).append(o)

        # Return dict of computed object clusters
        return clusters

    def __find_suitable_subclusters(self, clusters, rank_load, r_tol=0.05):
        """Find suitable sub-clusters to bring rank closest and above average load."""
        # Bail out early if no clusters are available
        if not clusters:
            self._logger.info("No migratable clusters on rank")
            return []

        # Build dict of suitable clusters with their load
        n_inspect = 0
        suitable_subclusters = {}
        step = 100.0 / len(clusters)
        for i, v in enumerate(clusters.values()):
            # Determine maximum subcluster size
            n_o = min(self._max_objects_per_transfer, len(v))

            # Use combinatorial exploration or law of large number based subsampling
            j = None
            for j, c in enumerate(chain.from_iterable(
                    combinations(v, p)
                    for p in range(1, n_o + 1)) if self._deterministic_transfer else (
                    tuple(random.sample(v, p))
                    for p in nr.binomial(n_o, 0.5, n_o))):
                # Reject subclusters overshooting within relative tolerance
                reach_load = rank_load - sum([o.get_load() for o in c])
                if reach_load < (1.0 - r_tol) * self._average_load:
                    continue

                # Retain suitable subclusters with their respective distance and cluster
                suitable_subclusters[c] = reach_load

                # Limit number of returned suitable clusters
                if not self._deterministic_transfer and len(suitable_subclusters) > (
                        i + 1) * step:
                    break

            # Update number of inspected combinations
            n_inspect += j + 1

        # Return subclusters and cluster IDs sorted by achievable loads
        self._logger.info(
            f"Found {len(suitable_subclusters)} suitable subclusters amongst {n_inspect} inspected")
        return sorted(suitable_subclusters.keys(), key=suitable_subclusters.get)

    def execute(self, known_peers, phase: Phase, ave_load: float):
        """Perform object transfer stage."""
        # Initialize transfer stage
        n_transfers, n_rejects = self._intialize_transfer_stage(ave_load)

        # Iterate over ranks
        ranks = phase.get_ranks()
        rank_targets = self._get_ranks_to_traverse(ranks, known_peers)
        for r_src, targets in rank_targets.items():
            # Cluster migratiable objects on source rank
            clusters_src = self.__cluster_objects(r_src)
            self._logger.info(
                f"Constructed {len(clusters_src)} migratable clusters on rank {r_src.get_id()} with load: {r_src.get_load()}")

            # Identify and perform beneficial cluster swaps
            n_swaps = 0
            for o_src in clusters_src.values():
                swapped_cluster = False
                for r_try in targets:
                    # Iterate over target clusters
                    for o_try in self.__cluster_objects(r_try).values():
                        # Decide whether swap is beneficial
                        if self._criterion.compute(r_src, o_src, r_try, o_try) > 0.0:
                            # Perform swap
                            n_transfers += phase.transfer_objects(
                                r_src, o_src, r_try, o_try)
                            swapped_cluster = True
                            n_swaps += 1
                            break

                    # Break out from targets loop once one swap was performed
                    if swapped_cluster:
                        break

            # Report on swaps when some occurred
            if n_swaps:
                self._logger.info(
                    f"New rank {r_src.get_id()} load: {r_src.get_load()} after {n_swaps} cluster swaps")
                # In non-deterministic case skip subclustering when swaps passed
                if not self._deterministic_transfer:
                    continue

            # Iterate over suitable subclusters only when no swaps were possible
            for o_src in self.__find_suitable_subclusters(
                    self.__cluster_objects(r_src), r_src.get_load()):
                # Initialize destination information
                r_dst, c_dst = None, -math.inf

                # Use deterministic or probabilistic transfer method
                if self._deterministic_transfer:
                    # Initialize destination load information
                    objects_load = sum([o.get_load() for o in o_src])
                    l_dst = math.inf

                    # Select best destination with respect to criterion
                    for r_try in targets:
                        c_try = self._criterion.compute(
                            r_src, o_src, r_try)
                        if c_try <= 0.0:
                            continue
                        l_try = abs(r_try.get_load() + objects_load - ave_load)
                        if l_try < l_dst:
                            c_dst, r_dst, r_dst = c_try, r_try, r_try
                        elif l_try == l_dst and c_try > c_dst:
                            c_dst, r_dst = c_try, r_try
                else:
                    # Pseudo-randomly select transfer destination
                    r_dst, c_dst = self._randomly_select_target(
                        r_src, o_src, targets)
                    if not r_dst:
                        n_rejects += 1
                        continue

                # Transfer subcluster and break out if best criterion is positive
                if c_dst > 0.0:
                    n_transfers += phase.transfer_objects(r_src, o_src, r_dst)
                    break

            # Report on new load and exit from rank
            self._logger.info(
                f"New rank {r_src.get_id()} load: {r_src.get_load()} after {n_transfers} object transfers")

        # Return object transfer counts
        return len(ranks) - len(rank_targets), n_transfers, n_rejects
