import sys
import random

from logging import Logger
from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsRank import Rank
from ..Model.lbsMessage import Message
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import print_function_statistics, min_Hamming_distance
from ..Utils.exception_handler import exc_handler


class InformAndTransferAlgorithm(AlgorithmBase):
    """A concrete class for the 2-phase gossip+transfer algorithm."""

    def __init__(
        self,
        work_model,
        parameters: dict,
        lgr: Logger,
        rank_qoi: str,
        object_qoi: str):
        """Class constructor
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters
            rank_qoi: rank QOI to track
            object_qoi: object QOI to track."""

        # Call superclass init
        super(InformAndTransferAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Retrieve mandatory integer parameters
        self.__n_iterations = parameters.get("n_iterations")
        if not isinstance(self.__n_iterations, int) or self.__n_iterations < 0:
            self._logger.error(
                f"Incorrect provided number of algorithm iterations: {self.__n_iterations}")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__n_rounds = parameters.get("n_rounds")
        if not isinstance(self.__n_rounds, int) or self.__n_rounds < 0:
            self._logger.error(
                f"Incorrect provided number of information rounds: {self.__n_rounds}")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__fanout = parameters.get("fanout")
        if not isinstance(self.__fanout, int) or self.__fanout < 0:
            self._logger.error(f"Incorrect provided information fanout {self.__fanout}")
            sys.excepthook = exc_handler
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
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Try to instantiate object transfer strategy
        strat_name = parameters.get("transfer_strategy")
        self.__transfer_strategy = TransferStrategyBase.factory(
            strat_name.title(),
            parameters,
            self.__transfer_criterion,
            lgr=self._logger)
        if not self.__transfer_strategy:
            self._logger.error(f"Could not instantiate a transfer strategy of type {strat_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Initialize empty dictionary of known peers
        self.__known_peers = {}

    def __initialize_message(self, r_snd: Rank, rank_set: set, f: int):
        """Initialize message to be sent to selected peers."""
        # Make rank aware of itself
        self.__known_peers[r_snd] = {r_snd}

        # Create initial message spawned from rank
        msg = Message(0, self.__known_peers[r_snd])

        # Broadcast message to pseudo-random sample of ranks excluding self
        return random.sample(
            list(rank_set.difference([r_snd])), min(f, len(rank_set) - 1)), msg

    def __forward_message(self, i: int, r: Rank, loads: set, f:int):
        """Forward information message to sample of selected peers."""
        # Create load message tagged at given information round
        msg = Message(i, {
            "loads": r.get_known_loads()})

        # Compute complement of set of known peers
        complement = set(r.get_known_loads()).difference([r])

        # Forward message to pseudo-random sample of ranks
        return random.sample(
            list(complement), min(f, len(complement))), msg

    def __information_stage(self):
        """Execute information stage."""

        # Build set of all ranks in the phase
        rank_set = set(self._rebalanced_phase.get_ranks())

        # Initialize information messages and known peers
        self._logger.info(
            f"Initializing information messages with fanout={self.__fanout}")
        messages = {}

        # Iterate over all ranks
        for r_snd in rank_set:
            # Collect message when destination list is not empty
            dst, msg = self.__initialize_message(r_snd, rank_set, self.__fanout)
            for r_rcv in dst:
                messages.setdefault(r_rcv, []).append(msg)

        # Process all messages of first round
        for r_rcv, m_rcv in messages.items():
            for m in m_rcv:
                # Process message by recipient
                self.__known_peers[r_rcv].update(m.get_support())

        # Report on gossiping status when requested
        for r in rank_set:
            self._logger.info(
                f"peers known to rank {r.get_id()}: "
                f"{[r_k.get_id() for r_k in self.__known_peers.get(r, {})]}")
        sys.exit(1)
        # Forward messages for as long as necessary and requested
        for i in range(1, self.__n_rounds):
            # Initiate next information round
            self._logger.debug(f"Performing message forwarding round {i}")
            messages.clear()

            # Iterate over all ranks
            for r_snd in rank_set:
                # Collect message when destination list is not empty
                dst, msg = self.__forward_message(
                    i, r_snd, rank_set, self.__fanout)
                for r_rcv in dst:
                    messages.setdefault(r_rcv, []).append(msg)

            # Process all messages of first round
            for r_rcv, msg_lst in messages.items():
                for m in msg_lst:
                    self.__process_message(r_rcv, m)

            # Report on gossiping status when requested
            for p in rank_set:
                self._logger.debug(
                    f"information known to rank {p.get_id()}: "
                    f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

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
            self.__information_stage()

            # Then execute transfer stage
            n_ignored, n_transfers, n_rejects = self.__transfer_strategy.execute(
                self._rebalanced_phase, statistics["average load"])
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
                lambda x: self._work_model.compute(x),
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
