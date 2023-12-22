import math
import random
import time
from itertools import chain, combinations
from logging import Logger

import numpy.random as nr

from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsRank import Rank
from ..Model.lbsPhase import Phase


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

        # Initialize maximum number of subclusters
        self._max_subclusters = parameters.get("max_subclusters", math.inf)
        self._logger.info(
            f"Maximum number of visited subclusters: {self._max_subclusters}")

        # Initialize cluster swap relative threshold
        self._cluster_swap_rtol = parameters.get("cluster_swap_rtol",0.05)
        self._logger.info(
            f"Relative tolerance for cluster swaps: {self._cluster_swap_rtol}")

        # Initialize global cluster swapping counters
        self.__n_swaps, self.__n_swap_tries = 0, 0

        # Initialize global subclustering counters
        self.__n_sub_skipped, self.__n_sub_transfers, self.__n_sub_tries = 0, 0, 0

    def __build_rank_clusters(self, rank: Rank, with_nullset) -> dict:
        """Cluster migratiable objects by shared block ID when available."""
        # Iterate over all migratable objects on rank
        clusters = {None: []} if with_nullset else {}
        for o in rank.get_migratable_objects():
            # Retrieve shared block ID and skip object without one
            sb_id = o.get_shared_block_id()
            if sb_id is None:
                continue

            # Add current object to its block ID cluster
            clusters.setdefault(sb_id, []).append(o)

        # Return dict of computed object clusters possibly randomized
        return clusters if self._deterministic_transfer else {
            k: clusters[k]
            for k in random.sample(clusters.keys(), len(clusters))}

    def __build_rank_subclusters(self, r_src: Rank) -> set:
        """Build subclusters to bring rank closest and above average load."""

        # Bail out early if no clusters are available
        if not (clusters := self.__build_rank_clusters(r_src, False).values()):
            self._logger.info(f"No migratable clusters on rank {r_src.get_id()}")
            return []

        # Time the duration of each search
        start_time = time.time()

        # Cache source rank load to avoid re-compute for each combination
        src_load = r_src.get_load()

        # Build dict of clusters with their load
        n_inspect, subclusters = 0, {}
        for i, v in enumerate(clusters):
            # Determine maximum subcluster size
            n_o = min(self._max_objects_per_transfer, (n_o_sub := len(v)))
            self._logger.debug(
                f"\t{n_o_sub} objects on cluster, maximum subcluster size: {n_o}")

            # Use combinatorial exploration or law of large number based subsampling
            j = 0
            for j, c in enumerate(chain.from_iterable(
                    combinations(v, p)
                    for p in range(1, n_o + 1)) if self._deterministic_transfer else (
                    tuple(random.sample(v, p))
                    for p in nr.binomial(n_o, 0.5, min(n_o, self._max_subclusters)))):
                # Reject subclusters overshooting within relative tolerance
                reach_load = src_load - sum([o.get_load() for o in c])
                if reach_load < (1.0 - self._cluster_swap_rtol) * self._average_load:
                    continue

                # Retain subclusters with their respective distance and cluster
                subclusters[c] = reach_load

            # Update number of inspected combinations
            n_inspect += j + 1

        # Return subclusters and cluster IDs sorted by achievable loads
        self._logger.info(
            f"Built {len(subclusters)} subclusters from {len(clusters)} clusters in {time.time() - start_time:.3f} seconds")
        return sorted(subclusters.keys(), key=subclusters.get)

    def __swap_clusters(self, phase: Phase, r_src: Rank, clusters_src:dict, targets: dict) -> int:
        """Perform feasible cluster swaps from given rank to possible targets."""
        # Initialize return variable
        n_rank_swaps = 0

        # Iterate over targets to identify and perform beneficial cluster swaps
        for r_try in targets if self._deterministic_transfer else random.sample(targets, len(targets)):
            # Escape targets loop if at least one swap already occurred
            if n_rank_swaps:
                break

            # Cluster migratiable objects on target rank
            clusters_try = self.__build_rank_clusters(r_try, True)
            self._logger.debug(
                f"Constructed {len(clusters_try)} migratable clusters on target rank {r_try.get_id()}")

            # Iterate over source clusters
            for k_src, o_src in clusters_src.items():
                # Iterate over target clusters
                for k_try, o_try in clusters_try.items():
                    # Decide whether swap is beneficial
                    c_try = self._criterion.compute(r_src, o_src, r_try, o_try)
                    self.__n_swap_tries += 1
                    if c_try > 0.0:
                        # Compute source cluster size only when necessary
                        sz_src = sum([o.get_load() for o in o_src])
                        if  c_try > self._cluster_swap_rtol * sz_src:
                            # Perform swap
                            self._logger.debug(
                                f"Swapping cluster {k_src} of size {sz_src} with cluster {k_try} on {r_try.get_id()}")
                            self._n_transfers += phase.transfer_objects(
                                r_src, o_src, r_try, o_try)
                            del clusters_try[k_try]
                            n_rank_swaps += 1
                            break
                        else:
                            # Reject swap
                            self._n_rejects += len(o_src) + len(o_try)

        # Return number of swaps performed from rank
        n_rank_swaps = 0

    def __transfer_subclusters(self, phase: Phase, r_src: Rank, targets: dict, ave_load: float) -> None:
        """Perform feasible subcluster transfers from given rank to possible targets."""
        # Iterate over source subclusters
        for o_src in self.__build_rank_subclusters(r_src):
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
                        c_dst, r_dst, l_dst = c_try, r_try, l_try
                    elif l_try == l_dst and c_try > c_dst:
                        c_dst, r_dst = c_try, r_try
            else:
                # Pseudo-randomly select transfer destination
                r_dst, c_dst = self._randomly_select_target(
                    r_src, o_src, targets)
                l_dst = r_dst.get_load()

            #  Decide whether transfer is beneficial
            self.__n_sub_tries += 1
            if c_dst > 0.0:
                # Transfer subcluster and break out
                self._logger.info(
                    f"Transferring subcluster with {len(o_src)} objects to rank {r_dst.get_id()}")
                self._n_transfers += phase.transfer_objects(
                    r_src, o_src, r_dst)
                self.__n_sub_transfers += 1
                break
            else:
                # Reject subcluster transfer
                self._n_rejects += len(o_src)


    def execute(self, known_peers, phase: Phase, ave_load: float):
        """Perform object transfer stage."""
        # Initialize transfer stage
        self._initialize_transfer_stage(ave_load)

        # Iterate over ranks
        rank_targets = self._get_ranks_to_traverse(phase.get_ranks(), known_peers)
        for r_src, targets in rank_targets.items():
            # Cluster migratable objects on source rank
            clusters_src = self.__build_rank_clusters(r_src, True)
            self._logger.debug(
                f"Constructed {len(clusters_src)} migratable clusters on source rank {r_src.get_id()}")

            # Perform feasible cluster swaps from given rank to possible targets
            if (n_rank_swaps := self.__swap_clusters(phase, r_src, clusters_src, targets)):
                # Report on swaps when some occurred
                self.__n_swaps += n_rank_swaps
                self._logger.debug(
                    f"New rank {r_src.get_id()} load: {r_src.get_load()} after {n_rank_swaps} cluster swaps")

                # In non-deterministic case skip subclustering when swaps passed
                if not self._deterministic_transfer:
                    self.__n_sub_skipped += 1
                    continue

            # Perform feasible subcluster swaps from given rank to possible targets
            self.__transfer_subclusters(phase, r_src, targets, ave_load)

            # Report on new load and exit from rank
            self._logger.debug(
                f"Rank {r_src.get_id()} load: {r_src.get_load()} after {self._n_transfers} object transfers")

        # Report on global transfer statistics
        n_ranks = len(phase.get_ranks())
        self._logger.info(
            f"Swapped {self.__n_swaps} cluster pairs amongst {self.__n_swap_tries} tries ({100 * self.__n_swaps / self.__n_swap_tries:.2f}%)")
        if self.__n_sub_tries:
            self._logger.info(
                f"Transferred {self.__n_sub_transfers} subcluster amongst {self.__n_sub_tries} tries ({100 * self.__n_sub_transfers / self.__n_sub_tries:.2f}%)")
        if self.__n_sub_skipped:
            self._logger.info(
                f"Skipped subclustering for {self.__n_sub_skipped} ranks ({100 * self.__n_sub_skipped / n_ranks:.2f}%)")

        # Return object transfer counts
        return n_ranks - len(rank_targets), self._n_transfers, self._n_rejects
