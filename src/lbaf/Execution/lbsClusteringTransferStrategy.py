import math
import random
import time
from itertools import chain, combinations
from logging import Logger

import numpy.random as nr

from .lbsTransferStrategyBase import TransferStrategyBase
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

        # Initialize cluster swap relative threshold
        self._cluster_swap_rtol = parameters.get("cluster_swap_rtol",0.05)
        self._logger.info(
            f"Relative tolerance for cluster swaps: {self._cluster_swap_rtol}")

    def __build_rank_clusters(self, rank, with_nullset):
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

    def __build_rank_subclusters(self, clusters, rank_load):
        """Build subclusters to bring rank closest and above average load."""

        # Bail out early if no clusters are available
        if not clusters:
            self._logger.info("No migratable clusters on rank")
            return []

        # Time the duration of each search
        start_time = time.time()

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
                    for p in nr.binomial(n_o, 0.5, min(n_o, 10)))):
                # Reject subclusters overshooting within relative tolerance
                reach_load = rank_load - sum([o.get_load() for o in c])
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

    def execute(self, known_peers, phase: Phase, ave_load: float):
        """Perform object transfer stage."""
        # Initialize transfer stage
        self._initialize_transfer_stage(ave_load)
        n_swaps, n_swap_tries, n_sub_transfers, n_sub_tries = 0, 0, 0, 0

        # Iterate over ranks
        ranks = phase.get_ranks()
        rank_targets = self._get_ranks_to_traverse(ranks, known_peers)
        for r_src, targets in rank_targets.items():
            # Cluster migratiable objects on source rank
            clusters_src = self.__build_rank_clusters(r_src, True)
            self._logger.debug(
                f"Constructed {len(clusters_src)} migratable clusters on source rank {r_src.get_id()}")

            # Identify and perform beneficial cluster swaps
            n_rank_swaps = 0
            for r_try in targets if self._deterministic_transfer else random.sample(
                    targets, len(targets)):
                # Escape targets loop if at least one swap already occurred
                if n_rank_swaps:
                    break

                # Cluster migratiable objects on target rank
                clusters_try = self.__build_rank_clusters(r_try, True)
                self._logger.debug(
                    f"Constructed {len(clusters_try)} migratable clusters on target rank {r_try.get_id()}")

                # Iterate over potential targets to try to swap clusters
                for k_src, o_src in clusters_src.items():
                    # Iterate over target clusters
                    for k_try, o_try in clusters_try.items():
                        # Decide whether swap is beneficial
                        c_try = self._criterion.compute(r_src, o_src, r_try, o_try)
                        n_swap_tries += 1
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

            # Report on swaps when some occurred
            if n_rank_swaps:
                n_swaps += n_rank_swaps
                self._logger.debug(
                    f"New rank {r_src.get_id()} load: {r_src.get_load()} after {n_rank_swaps} cluster swaps")

                # In non-deterministic case skip subclustering when swaps passed
                if not self._deterministic_transfer:
                    continue

            # Iterate over subclusters only when no swaps were possible
            for o_src in self.__build_rank_subclusters(
                    self.__build_rank_clusters(r_src, False).values(), r_src.get_load()):
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
                n_sub_tries += 1
                if c_dst > 0.0:
                    # Transfer subcluster and break out
                    self._logger.info(
                        f"Transferring subcluster with {len(o_src)} objects to rank {r_dst.get_id()}")
                    self._n_transfers += phase.transfer_objects(
                        r_src, o_src, r_dst)
                    n_sub_transfers += 1
                    break
                else:
                    # Reject subcluster transfer
                    self._n_rejects += len(o_src)

            # Report on new load and exit from rank
            self._logger.debug(
                f"Rank {r_src.get_id()} load: {r_src.get_load()} after {self._n_transfers} object transfers")

        # Report on global transfer statistics
        self._logger.info(
            f"Swapped {n_swaps} cluster pairs amongst {n_swap_tries} tries ({100 * n_swaps / n_swap_tries:.2f}%)")
        if n_sub_tries:
            self._logger.info(
                f"Transferred {n_sub_transfers} subcluster amongst {n_sub_tries} tries ({100 * n_sub_transfers / n_sub_tries:.2f}%)")

        # Return object transfer counts
        return len(ranks) - len(rank_targets), self._n_transfers, self._n_rejects
