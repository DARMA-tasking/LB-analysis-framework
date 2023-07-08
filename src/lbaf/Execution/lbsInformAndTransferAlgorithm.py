import random
from logging import Logger

from ..IO.lbsStatistics import min_Hamming_distance, print_function_statistics
from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsRank import Rank
from ..Model.lbsMessage import Message
from ..IO.lbsStatistics import print_function_statistics, min_Hamming_distance


class InformAndTransferAlgorithm(AlgorithmBase):
    """A concrete class for the 2-phase gossip+transfer algorithm."""

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
        super(InformAndTransferAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Retrieve mandatory integer parameters
        self.__n_iterations = parameters.get("n_iterations")
        if not isinstance(self.__n_iterations, int) or self.__n_iterations < 0:
            self._logger.error(f"Incorrect provided number of algorithm iterations: {self.__n_iterations}")
            raise SystemExit(1)
        self.__n_rounds = parameters.get("n_rounds")
        if not isinstance(self.__n_rounds, int) or self.__n_rounds < 0:
            self._logger.error(f"Incorrect provided number of information rounds: {self.__n_rounds}")
            raise SystemExit(1)
        self.__fanout = parameters.get("fanout")
        if not isinstance(self.__fanout, int) or self.__fanout < 0:
            self._logger.error(f"Incorrect provided information fanout {self.__fanout}")
            raise SystemExit(1)
        self._logger.info(
            f"Instantiated with {self.__n_iterations} iterations, {self.__n_rounds} rounds, fanout {self.__fanout}")

        # Try to instantiate object transfer criterion
        crit_name = parameters.get("criterion")
        self.__transfer_criterion = CriterionBase.factory(
            crit_name,
            self._work_model,
            logger=self._logger)
        if not self.__transfer_criterion:
            self._logger.error(f"Could not instantiate a transfer criterion of type {crit_name}")
            raise SystemExit(1)

        # Try to instantiate object transfer strategy
        strat_name = parameters.get("transfer_strategy")
        self.__transfer_strategy = TransferStrategyBase.factory(
            strat_name.title(),
            parameters,
            self.__transfer_criterion,
            logger=self._logger)
        if not self.__transfer_strategy:
            self._logger.error(f"Could not instantiate a transfer strategy of type {strat_name}")
            raise SystemExit(1)

        # No information about peers is known initially
        self.__known_peers = {}

    def get_known_peers(self):
        """Return all known peers."""
        return self.__known_peers

    def __process_message(self, r_rcv: Rank, m: Message):
        """Process message received by rank."""
        # Make rank aware of itself
        if r_rcv not in self.__known_peers:
            self.__known_peers[r_rcv] = {r_rcv}

        # Process the message
        self.__known_peers[r_rcv].update(m.get_support())

    def __forward_message(self, i: int, r_snd: Rank, f:int):
        """Forward information message to rank peers sampled from known ones."""
        # Make rank aware of itself
        if r_snd not in self.__known_peers:
            self.__known_peers[r_snd] = {r_snd}

        # Create load message tagged at given information round
        msg = Message(i, self.__known_peers[r_snd])

        # Compute complement of set of known peers
        complement = self.__known_peers[r_snd].difference({r_snd})

        # Forward message to pseudo-random sample of ranks
        return random.sample(
            list(complement), min(f, len(complement))), msg

    def __execute_information_stage(self):
        """Execute information stage."""
        # Build set of all ranks in the phase
        rank_set = set(self._rebalanced_phase.get_ranks())

        # Initialize information messages and known peers
        messages, self.__known_peers = {}, {}
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
                    f"Peers known to rank {r.get_id()}: {[r_k.get_id() for r_k in k_p]}")

        # Report on final know information ratio
        n_k = sum([len(k_p) for k_p in self.__known_peers.values() if k_p]) / n_r
        self._logger.info(
            f"Average number of peers known to ranks: {n_k} ({100 * n_k / n_r:.2f}% of {n_r})")

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """ Execute 2-phase information+transfer algorithm on Phase with index p_id."""
        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, distributions, statistics)

        # Set phase to be used by transfer criterion
        self.__transfer_criterion.set_phase(self._rebalanced_phase)

        # Retrieve totat work from computed statistics
        total_work = statistics["total work"][-1]

        # Perform requested number of load-balancing iterations
        for i in range(self.__n_iterations):
            self._logger.info(f"Starting iteration {i + 1} with total work of {total_work}")

            # Start with information stage
            self.__execute_information_stage()

            # Then execute transfer stage
            n_ignored, n_transfers, n_rejects = self.__transfer_strategy.execute(
                self.__known_peers, self._rebalanced_phase, statistics["average load"])
            n_proposed = n_transfers + n_rejects
            if n_proposed:
                self._logger.info(
                    f"{n_proposed} proposed transfers, {n_transfers} occurred, {n_rejects} rejected "
                    f"({100. * n_rejects / n_proposed:.4}%)")
            else:
                self._logger.info("No transfers were proposed")

            # Report iteration statistics
            self._logger.info(f"Iteration complete ({n_ignored} skipped ranks)")

            # Compute and report iteration work statistics
            print_function_statistics(
                self._rebalanced_phase.get_ranks(),
                lambda x: self._work_model.compute(x),  # pylint:disable=W0108:unnecessary-lambda
                f"iteration {i + 1} rank work",
                self._logger)

            # Update run distributions and statistics
            self._update_distributions_and_statistics(distributions, statistics)

            # Compute current arrangement
            arrangement = tuple(
                v for _, v in sorted(
                    {o.get_id(): p.get_id()
                     for p in self._rebalanced_phase.get_ranks()
                     for o in p.get_objects()}.items()))
            self._logger.debug(f"Iteration {i + 1} arrangement: {arrangement}")

            # Report minimum Hamming distance when minimax optimum is available
            if a_min_max:
                hd_min = min_Hamming_distance(arrangement, a_min_max)
                self._logger.info(
                    f"Iteration {i + 1} minimum Hamming distance to optimal arrangements: {hd_min}")
                statistics["minimum Hamming distance to optimum"].append(hd_min)

        # Report final mapping in debug mode
        self._report_final_mapping(self._logger)
