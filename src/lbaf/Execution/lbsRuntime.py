import sys
from logging import Logger

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Execution.lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import compute_function_statistics, min_Hamming_distance
from ..Utils.exception_handler import exc_handler


class Runtime:
    """ A class to handle the execution of the LBS
    """

    def __init__(self, phases: list, work_model: dict, algorithm: dict, arrangements: list, logger: Logger):
        """ Class constructor:
            phases: list of Phase instances
            work_model: dictionary with work model name and optional parameters
            algorithm: dictionary with algorithm name and parameters
            a: arrangements that minimize maximum work
            logger: logger for output messages
        """

        # Assign logger to instance variable
        self.__logger = logger

        # Keep track of possibly empty list of arrangements with minimax work
        self.__logger.info(
            f"Instantiating runtime with {len(arrangements)} optimal arrangements for Hamming distance comparison")
        self.__a_min_max = arrangements

        # If no LBS phase was provided, do not do anything
        if not phases or not isinstance(phases, list):
            self.__logger.error("Could not create a LBS runtime without a list of phases")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__phases = phases

        # Instantiate work model
        self.__work_model = WorkModelBase.factory(
            work_model.get("name"),
            work_model.get("parameters", {}),
            self.__logger)

        # Instantiate balancing algorithm
        self.__algorithm = AlgorithmBase.factory(
            algorithm.get("name"),
            algorithm.get("parameters", {}),
            self.__work_model,
            lgr=self.__logger)
        if not self.__algorithm:
            self.__logger.error(
                f"Could not instantiate an algorithm of type {self.__algorithm}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Initialize run distributions and statistics
        phase_0 = self.__phases[0]
        self.distributions = {}
        _, _, l_ave, _, _, _, _, _ = compute_function_statistics(
            phase_0.get_ranks(),
            lambda x: x.get_load())
        self.statistics = {"average load": l_ave}

        # Compute initial arrangement
        arrangement = tuple(
            v for _, v in sorted({
                o.get_id(): p.get_id()
                for p in phase_0.get_ranks()
                for o in p.get_objects()}.items()))
        self.__logger.debug(f"Iteration 0 arrangement: {arrangement}")

        # Report minimum Hamming distance when minimax optimum is available
        if self.__a_min_max:
            hd_min = min_Hamming_distance(arrangement, self.__a_min_max)
            self.statistics["minimum Hamming distance to optimum"] = [hd_min]
            self.__logger.info(f"Iteration 0 minimum Hamming distance to optimal arrangements: {hd_min}")

    def get_work_model(self):
        """ Return runtime work model."""

        return self.__work_model

    def execute(self):
        """ Launch runtime execution."""

        # Execute balancing algorithm
        self.__logger.info(f"Executing {type(self.__algorithm).__name__}")
        self.__algorithm.execute(
            self.__phases,
            self.distributions,
            self.statistics,
            self.__a_min_max)
