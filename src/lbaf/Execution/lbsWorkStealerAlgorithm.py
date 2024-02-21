import random
import time
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsRank import Rank
from ..Model.lbsMessage import Message
from ..IO.lbsStatistics import min_Hamming_distance, print_function_statistics


class WorkStealerAlgorithm(AlgorithmBase):
    """A concrete class simulating execution."""

    def __init__(
        self,
        work_model,
        parameters: dict,
        lgr: Logger,
        rank_qoi: str,
        object_qoi: str):
        """Class constructor.

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        :param rank_qoi: rank QOI to track
        :param object_qoi: object QOI to track.
        """
        # Call superclass init
        super(WorkStealerAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Initialize cluster swap relative threshold
        self.__cluster_swap_rtol = parameters.get("cluster_swap_rtol", 0.05)
        self._logger.info(
            f"Relative tolerance for cluster swaps: {self.__cluster_swap_rtol}")

        # Initialize global cluster swapping counters
        self.__n_swaps, self.__n_swap_tries = 0, 0

        # Try to instantiate object transfer criterion
        crit_name = parameters.get("criterion")
        self.__transfer_criterion = CriterionBase.factory(
            crit_name,
            self._work_model,
            logger=self._logger)
        if not self.__transfer_criterion:
            self._logger.error(f"Could not instantiate a transfer criterion of type {crit_name}")
            raise SystemExit(1)

        # Optional target imbalance for early termination of iterations
        self.__target_imbalance = parameters.get("target_imbalance", 0.0)

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
                  c_try = self.__transfer_criterion.compute(r_src, o_src, r_try, o_try)
                  self.__n_swap_tries += 1
                  if c_try > 0.0:
                      # Compute source cluster size only when necessary
                      sz_src = sum([o.get_load() for o in o_src])
                      if  c_try > self.__cluster_swap_rtol * sz_src:
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

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """ Simulate execution."""
        # Implement a discrete simulator
        #  - Once a rank completes its task, it "steals" a random cluster from a random rank
        #  - Output time at the end
        pass
