import sys
import math
import random
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from .lbsCriterionBase import CriterionBase
from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import print_function_statistics, inverse_transform_sample, min_Hamming_distance
from ..Utils.exception_handler import exc_handler


class InformAndTransferAlgorithm(AlgorithmBase):
    """ A concrete class for the 2-phase gossip+transfer algorithm."""

    def __init__(self, work_model, parameters: dict, lgr: Logger, rank_qoi: str, object_qoi: str):
        """ Class constructor
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
        self.__transfer_criterion = CriterionBase.factory(
            parameters.get("criterion"),
            self._work_model,
            lgr=self._logger)
        if not self.__transfer_criterion:
            self._logger.error(f"Could not instantiate a transfer criterion of type {self.__criterion_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Try to instantiate object transfer strategy
        strat_name = "Recursive"
        self.__transfer_strategy = TransferStrategyBase.factory(
            strat_name,
            parameters,
            self.__transfer_criterion,
            lgr=self._logger)
        if not self.__transfer_strategy:
            self._logger.error(f"Could not instantiate a transfer strategy of type {strat_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Assign optional parameters
        self.__deterministic_transfer = parameters.get("deterministic_transfer", False)
        self.__max_objects_per_transfer = parameters.get("max_objects_per_transfer", math.inf)

    def information_stage(self):
        """ Execute information stage."""

        # Build set of all ranks in the phase
        rank_set = set(self._phase.get_ranks())

        # Initialize information messages
        self._logger.info(f"Initializing information messages with fanout={self.__fanout}")
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
                self._logger.debug(f"information known to rank {p.get_id()}: "
                                    f"{[p_u.get_id() for p_u in p.get_known_loads()]}")

        # Build reverse lookup of ranks to those aware of them
        for p in rank_set:
            # Skip non-loaded ranks
            if not p.get_load():
                continue

    def recursive_extended_search(self, pick_list, object_list, c_fct, n_o, max_n_o):
        """ Recursively extend search to other objects."""

        # Fail when no more objects available or maximum depth is reached
        if not pick_list or n_o >= max_n_o:
            return False

        # Pick one object and move it from one list to the other
        o = random.choice(pick_list)
        pick_list.remove(o)
        object_list.append(o)
        n_o += 1

        # Decide whether criterion allows for transfer
        if c_fct(object_list) < 0.:
            # Transfer is not possible, recurse further
            return self.recursive_extended_search(
                pick_list, object_list, c_fct, n_o, max_n_o)
        else:
            # Succeed when criterion is satisfied
            return True

    def execute(self, phases: list, distributions: dict, statistics: dict, a_min_max):
        """ Execute 2-phase gossip+transfer algorithm on Phase instance."""

        # Ensure that a list with at least one phase was provided
        if not phases or not isinstance(phases, list) or not isinstance((phase := phases[0]), Phase):
            self._logger.error(f"Algorithm execution requires a Phase instance")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._phase = phase
        self.__transfer_criterion.set_phase(phase)

        # Initialize run distributions and statistics
        self.update_distributions_and_statistics(distributions, statistics)

        # Keep track of average load
        self.__average_load = statistics.get("average load", math.nan)

        # Perform requested number of load-balancing iterations
        for i in range(self.__n_iterations):
            self._logger.info(f"Starting iteration {i + 1}")

            # Start with information stage
            self.information_stage()

            # Then execute transfer stage
            n_ignored, n_transfers, n_rejects = self.__transfer_strategy.execute(self._phase)
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
                self._phase.get_ranks(),
                lambda x: self._work_model.compute(x),
                f"iteration {i + 1} rank work",
                self._logger)

            # Update run distributions and statistics
            self.update_distributions_and_statistics(distributions, statistics)

            # Compute current arrangement
            arrangement = tuple(
                v for _, v in sorted(
                    {o.get_id(): p.get_id()
                     for p in self._phase.get_ranks()
                     for o in p.get_objects()}.items()))
            self._logger.debug(f"Iteration {i + 1} arrangement: {arrangement}")

            # Report minimum Hamming distance when minimax optimum is available
            if a_min_max:
                hd_min = min_Hamming_distance(arrangement, a_min_max)
                self._logger.info(
                    f"Iteration {i + 1} minimum Hamming distance to optimal arrangements: {hd_min}")
                statistics["minimum Hamming distance to optimum"].append(hd_min)

        # Report final mapping in debug mode
        self.report_final_mapping(self._logger)

