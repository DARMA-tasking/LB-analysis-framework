import sys
import math
from logging import Logger

from ..Model.lbsPhase import Phase
from ..Model.lbsWorkModelBase import WorkModelBase
from ..Execution.lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import print_function_statistics, compute_function_statistics, min_Hamming_distance


class Runtime:
    """ A class to handle the execution of the LBS
    """

    def __init__(
        self, phase: Phase,
        work_model: dict,
        algorithm: dict,
        arrangements: list,
        logger: Logger):
        """ Class constructor:
            phase: phase instance
            work_model: dictionary with work model name and optional parameters
            algorithm: dictionary with algorithm name and parameters
            a: arrangements that minimize maximum work
            logger: logger for output messages
        """

        # Keep track of possibly empty list of arrangements with minimax work
        self.__a_min_max = arrangements

        # Assign logger to instance variable
        self.__logger = logger

        # If no LBS phase was provided, do not do anything
        if not isinstance(phase, Phase):
            self.__logger.warning("Could not create a LBS runtime without a phase")
            return
        else:
            self.__phase = phase

        # Instantiate work model
        self.__work_model = WorkModelBase.factory(
            work_model.get("name"),
            work_model.get("parameters", {}),
            lgr=self.__logger)
        if not self.__work_model:
            self.__logger.error(f"Could not instantiate a work model of type {self.__work_model}")
            sys.exit(1)

        # Instantiate balancing algorithm
        self.__algorithm = AlgorithmBase.factory(
            algorithm.get("name"),
            algorithm.get("parameters", {}),
            self.__work_model,
            lgr=self.__logger)
        if not self.__algorithm:
            self.__logger.error(f"Could not instantiate an algorithm of type {self.__algorithm}")
            sys.exit(1)

        # Initialize run distributions and statistics
        self.distributions = {}
        _, _, l_ave, _, _, _, _, _ = compute_function_statistics(
            self.__phase.get_ranks(),
            lambda x: x.get_load())
        self.statistics = {"average load": l_ave}

        # Compute load, volume and work statistics
        self.__logger.info(f"Instantiated with {len(arrangements)} optimal arrangements for Hamming distance comparison")
        print_function_statistics(
            self.__phase.get_ranks(),
            lambda x: self.__work_model.compute(x),
            "initial rank works",
            logger=self.__logger)

        # Compute initial arrangement
        arrangement = tuple(
            v for _, v in sorted({
                o.get_id(): p.get_id()
                for p in self.__phase.get_ranks() for o in p.get_objects()
                }.items()))
        self.__logger.debug(f"Iteration 0 arrangement: {arrangement}")

        # Report minimum Hamming distance when minimax optimum is available
        if self.__a_min_max:
            hd_min = min_Hamming_distance(arrangement, self.__a_min_max)
            self.statistics["minimum Hamming distance to optimum"] = [hd_min]
            self.__logger.info(f"Iteration 0 minimum Hamming distance to optimal arrangements: {hd_min}")


    def execute(self):
        """ Launch runtime execution
        """

        # Execute balancing algorithm
        self.__logger.info(f"Executing {type(self.__algorithm).__name__}")
        self.__algorithm.execute(
            self.__phase,
            self.distributions,
            self.statistics,
            self.__a_min_max)
