from logging import Logger

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Execution.lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import compute_function_statistics, min_Hamming_distance


class Runtime:
    """A class to handle the execution of the LBS."""

    def __init__(self, phases: dict, work_model: dict, algorithm: dict, arrangements: list, logger: Logger,
                rank_qoi: str, object_qoi: str):
        """Class constructor.

        :param phases: dictionary of Phase instances
        :param work_model: dictionary with work model name and optional parameters
        :param algorithm: dictionary with algorithm name and parameters
        :param arrangements: arrangements that minimize maximum work
        :param logger: logger for output messages
        :param rank_qoi: rank QOI name whose distributions are to be tracked
        :param object_qoi: object QOI name whose distributions are to be tracked.
        """
        # Assign logger to instance variable
        self.__logger = logger

        # Keep track of possibly empty list of arrangements with minimax work
        self.__logger.info(
            f"Instantiating runtime with {len(arrangements)} optimal arrangements for Hamming distance")
        self.__a_min_max = arrangements

        # If no LBS phase was provided, do not do anything
        if not phases or not isinstance(phases, dict):
            self.__logger.error(
                "Could not create a runtime without a dictionnary of phases")
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
            self.__logger,
            rank_qoi,
            object_qoi)
        if not self.__algorithm:
            self.__logger.error(
                f"Could not instantiate an algorithm of type {self.__algorithm}")
            raise SystemExit(1)

        # Initialize run distributions and statistics
        phase_0 = self.__phases[min(self.__phases.keys())]
        self.__distributions = {}
        l_stats = compute_function_statistics(
            phase_0.get_ranks(),
            lambda x: x.get_load())
        self.__statistics = {"average load": l_stats.get_average()}

        # Compute initial arrangement
        arrangement = tuple(
            v for _, v in sorted({
                o.get_id(): p.get_id()
                for p in phase_0.get_ranks()
                for o in p.get_objects()}.items()))
        self.__logger.debug(f"Phase 0 arrangement: {arrangement}")

        # Report minimum Hamming distance when minimax optimum is available
        if self.__a_min_max:
            hd_min = min_Hamming_distance(arrangement, self.__a_min_max)
            self.__statistics["minimum Hamming distance to optimum"] = [hd_min]
            self.__logger.info(f"Phase 0 minimum Hamming distance to optimal arrangements: {hd_min}")

    def get_work_model(self):
        """Return runtime work model."""
        return self.__work_model

    def get_distributions(self):
        """Return runtime distributions."""
        return self.__distributions

    def get_statistics(self):
        """Return runtime statistics."""
        return self.__statistics

    def execute(self, p_id: int, phase_increment=0):
        """Execute runtime for single phase with given ID or all (-1)."""

        # Execute balancing algorithm
        self.__logger.info(
            f"Executing {type(self.__algorithm).__name__} for "
            + ("all phases" if p_id < 0 else f"phase {p_id}"))
        self.__algorithm.execute(
            p_id,
            self.__phases,
            self.__distributions,
            self.__statistics,
            self.__a_min_max)

        # Retrieve possibly null rebalanced phase and return it
        if (pp := self.__algorithm.get_rebalanced_phase()):
            pp.set_id((pp_id := pp.get_id() + phase_increment))
            self.__logger.info(f"Created rebalanced phase {pp_id}")
        return pp
