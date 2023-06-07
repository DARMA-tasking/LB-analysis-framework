import sys

from logging import Logger
from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from .lbsTransferStrategyBase import TransferStrategyBase
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

    def __information_stage(self):
        """Execute information stage."""
        # Build set of all ranks in the phase
        rank_set = set(self._rebalanced_phase.get_ranks())

        # Initialize information messages
        self._logger.info(
            f"Initializing information messages with fanout={self.__fanout}")
        information_round = 1
        messages = {}

        # Iterate over all ranks
        for p_snd in rank_set:
            # Reset load information known by sender
            p_snd.reset_all_load_information()

            # Collect message when destination list is not empty
            dst, msg = p_snd.initialize_message(rank_set, self.__fanout)
            for p_rcv in dst:
                messages.setdefault(p_rcv, []).append(msg)

        # Process all messages of first round
        for p_rcv, msg_lst in messages.items():
            for m in msg_lst:
                p_rcv.process_message(m)

        # Report on gossiping status when requested
        for p in rank_set:
            self._logger.debug(f"information known to rank {p.get_id()}: "
                                f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Forward messages for as long as necessary and requested
        while information_round < self.__n_rounds:
            # Initiate next gossiping round
            self._logger.debug(f"Performing message forwarding round {information_round}")
            information_round += 1
            messages.clear()

            # Iterate over all ranks
            for p_snd in rank_set:
                # Check whether rank must relay previously received message
                if p_snd.round_last_received + 1 == information_round:
                    # Collect message when destination list is not empty
                    dst, msg = p_snd.forward_message(information_round, rank_set, self.__fanout)
                    for p_rcv in dst:
                        messages.setdefault(p_rcv, []).append(msg)

            # Process all messages of first round
            for p_rcv, msg_lst in messages.items():
                for m in msg_lst:
                    p_rcv.process_message(m)

            # Report on gossiping status when requested
            for p in rank_set:
                self._logger.debug(
                    f"information known to rank {p.get_id()}: "
                    f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Build reverse lookup of ranks to those aware of them
        for p in rank_set:
            # Skip non-loaded ranks
            if not p.get_load():
                continue

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, a_min_max):
        """ Execute 2-phase gossip+transfer algorithm on Phase with index p_id."""
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
