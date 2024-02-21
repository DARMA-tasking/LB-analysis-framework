import random
import time
from logging import Logger
from collections import deque

from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsRank import Rank
from ..Model.lbsMessage import Message
from ..IO.lbsStatistics import min_Hamming_distance, print_function_statistics


class WorkStealingAlgorithm(AlgorithmBase):
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
        super(WorkStealingAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Initialize the discretion interval
        self.__discretion_interval = parameters.get("discretion_interval")

        # Initialize cluster swap relative threshold
        self.__cluster_swap_rtol = parameters.get("cluster_swap_rtol", 0.05)
        self.__logger.info(
            f"Relative tolerance for cluster swaps: {self.__cluster_swap_rtol}")

        # Initialize queue per rank
        self.__queue_per_rank = {}

        # Initialize global cluster swapping counters
        self.__n_swaps, self.__n_swap_tries = 0, 0

        # Try to instantiate object transfer criterion
        crit_name = parameters.get("criterion")
        self.__transfer_criterion = CriterionBase.factory(
            crit_name,
            self._work_model,
            logger=self.__logger)
        if not self.__transfer_criterion:
            self.__logger.error(f"Could not instantiate a transfer criterion of type {crit_name}")
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
            self.__logger.debug(
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
                            self.__logger.debug(
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

def __execute_stealing_stage(self):
        """Execute stealing stage."""
        # Build set of all ranks in the phase
        rank_set = set(self._rebalanced_phase.get_ranks())

        # Initialize information messages and known peers
        messages = {}
        n_r = len(rank_set)
        for r_snd in rank_set:
            # Make rank aware of itself
            self.__known_peers[r_snd] = {r_snd}

            # Create initial message spawned from rank
            msg = Message(0, {r_snd})

            # Broadcast message to random sample of ranks excluding self
            for r_rcv in random.sample(
                list(rank_set.difference({r_snd})), min(self.__fanout, n_r - 1)):
                messages.setdefault(r_rcv, []).append(msg)

        # Sanity check prior to forwarding iterations
        if (n_m := sum([len(m) for m in messages.values()])) != (n_c := n_r * self.__fanout):
            self._logger.error(
                f"Incorrect number of initial messages: {n_m} <> {n_c}")
        self._logger.info(
            f"Sent {n_m} initial information messages with fanout={self.__fanout}")

        # Process all received initial messages
        for r_rcv, m_rcv in messages.items():
            for m in m_rcv:
                # Process message by recipient
                self.__process_message(r_rcv, m)

        # Perform sanity check on first round of information aggregation
        n_k = 0
        for r in rank_set:
            # Retrieve and tally peers known to rank
            k_p = self.__known_peers.get(r, {})
            n_k += len(k_p)
            self._logger.debug(
                f"Peers known to rank {r.get_id()}: {[r_k.get_id() for r_k in k_p]}")
        if n_k != (n_c := n_c + n_r):
            self._logger.error(
                f"Incorrect total number of aggregated initial known peers: {n_k} <> {n_c}")

        # Forward messages for as long as necessary and requested
        for i in range(1, self.__n_rounds):
            # Initiate next information round
            self._logger.debug(f"Performing message forwarding round {i}")
            messages.clear()

            # Iterate over all ranks
            for r_snd in rank_set:
                # Collect message when destination list is not empty
                dst, msg = self.__forward_message(
                    i, r_snd, self.__fanout)
                for r_rcv in dst:
                    messages.setdefault(r_rcv, []).append(msg)

            # Process all messages of first round
            for r_rcv, msg_lst in messages.items():
                for m in msg_lst:
                    self.__process_message(r_rcv, m)

            # Report on known peers when requested
            for rank in rank_set:
                self._logger.debug(
                    f"Peers known to rank {rank.get_id()}: {[r_k.get_id() for r_k in k_p]}")

        # Report on final know information ratio
        n_k = sum([len(k_p) for k_p in self.__known_peers.values() if k_p]) / n_r
        self._logger.info(
            f"Average number of peers known to ranks: {n_k} ({100 * n_k / n_r:.2f}% of {n_r})")

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """ Simulate execution."""
        # Implement a discrete simulator
        #  - Once a rank completes its task, it "steals" a random cluster from a random rank
        #  - Output time at the end

        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, distributions, statistics)
        print_function_statistics(
            self._rebalanced_phase.get_ranks(),
            self._work_model.compute,
            "initial rank work",
            self._logger)
