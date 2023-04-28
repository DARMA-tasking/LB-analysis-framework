import abc
import sys

from ..IO.lbsStatistics import compute_function_statistics
from ..Model.lbsWorkModelBase import WorkModelBase
from ..Utils.exception_handler import exc_handler
from ..Utils.logging import get_logger, Logger


class AlgorithmBase:
    """An abstract base class of load/work balancing algorithms."""

    __metaclass__ = abc.ABCMeta

    _work_model: WorkModelBase
    _logger: Logger

    def __init__(self, work_model: WorkModelBase, parameters: dict, logger: Logger, rank_qoi: str, object_qoi: str):
        """Class constructor:
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters
            rank_qoi: rank QOI to track
            object_qoi: object QOI to track."""

        # Assert that a logger instance was passed
        if not isinstance(logger, Logger):
            get_logger().error(
                f"Incorrect type {type(logger)} passed instead of Logger instance")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._logger = logger

        # Assert that a work model base instance was passed
        if not isinstance(work_model, WorkModelBase):
            self._logger.error("Could not create an algorithm without a work model")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._work_model = work_model

        # Assert that a parameters dict was passed
        if not isinstance(parameters, dict):
            self._logger.error("Could not create an algorithm without a dictionary of parameters")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Assert that quantity of interest names are string
        if rank_qoi and not isinstance(rank_qoi, str):
            self._logger.error("Could not create an algorithm with non-string rank QOI name")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__rank_qoi = rank_qoi
        if object_qoi and not isinstance(object_qoi, str):
            self._logger.error("Could not create an algorithm with non-string object QOI name")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__object_qoi = object_qoi
        self._logger.info(
            f"Created base algorithm tracking rank {rank_qoi} and object {object_qoi}")

        # Initially no phase is associated to algorithm
        self._phase = None

        # Map global statistical QOIs to their computation methods
        self.__statistics = {
            ("ranks", lambda x: x.get_load()): {
                "minimum load": "minimum",
                "maximum load": "maximum",
                "load variance": "variance",
                "load imbalance": "imbalance"},
            ("largest_volumes", lambda x: x): {
                "number of communication edges": "cardinality",
                "maximum largest directed volume": "maximum",
                "total largest directed volume": "sum"},
            ("ranks", lambda x: self._work_model.compute(x)): {
                "minimum work": "minimum",
                "maximum work": "maximum",
                "total work": "sum",
                "work variance": "variance"}}

    @staticmethod
    def factory(
        algorithm_name:str,
        parameters: dict,
        work_model: WorkModelBase,
        lgr: Logger,
        rank_qoi: str,
        object_qoi:str):
        """Instantiate the necessary concrete algorithm."""

        # Load up available algorithms
        # pylint:disable=W0641,C0415
        from .lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
        from .lbsBruteForceAlgorithm import BruteForceAlgorithm
        from .lbsPhaseStepperAlgorithm import PhaseStepperAlgorithm
        # pylint:enable=W0641,C0415

        # Ensure that algorithm name is valid
        algorithm = locals()[algorithm_name + "Algorithm"]
        return algorithm(work_model, parameters, lgr, rank_qoi, object_qoi)
        try:
            # Instantiate and return object
            algorithm = locals()[algorithm_name + "Algorithm"]
            return algorithm(work_model, parameters, lgr, rank_qoi, object_qoi)
        except Exception as e:
            # Otherwise, error out
            lgr.error(f"Could not create an algorithm with name {algorithm_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1) from e

    def update_distributions_and_statistics(self, distributions: dict, statistics: dict):
        """Compute and update run distributions and statistics."""

        # Create or update distributions of object quantities of interest
        for object_qoi_name in tuple({"load", self.__object_qoi}):
            if not object_qoi_name:
                continue
            distributions.setdefault(f"object {object_qoi_name}", []).append(
                {o.get_id(): getattr(o, f"get_{object_qoi_name}")()
                 for o in self._phase.get_objects()})

        # Create or update distributions of rank quantities of interest
        for rank_qoi_name in tuple({"objects", "load", self.__rank_qoi}):
            if not rank_qoi_name or rank_qoi_name == "work":
                continue
            distributions.setdefault(f"rank {rank_qoi_name}", []).append(
                [getattr(p, f"get_{rank_qoi_name}")()
                 for p in self._phase.get_ranks()])
        distributions.setdefault("rank work", []).append(
            [self._work_model.compute(p) for p in self._phase.get_ranks()])

        # Create or update distributions of edge quantities of interest
        distributions.setdefault("sent", []).append(dict(
            self._phase.get_edge_maxima().items()))

        # Create or update statistics dictionary entries
        for (support, getter), stat_names in self.__statistics.items():
            for k, v in stat_names.items():
                stats = compute_function_statistics(
                    getattr(self._phase, f"get_{support}")(), getter)
                statistics.setdefault(k, []).append(getattr(stats, f"get_{v}")())

    def _report_final_mapping(self, logger):
        """Report final rank object mapping in debug mode."""

        for rank in self._phase.get_ranks():
            logger.debug(f"Rank {rank.get_id()}:")
            for o in rank.get_objects():
                comm = o.get_communicator()
                if comm:
                    logger.debug(f"Object {o.get_id()}:")
                    recv = comm.get_received().items()
                    if recv:
                        logger.debug("received from:")
                        for k, v in recv:
                            logger.debug(
                                f"object {k.get_id()} on rank {k.get_rank_id()}: {v}")
                    sent = comm.get_sent().items()
                    if sent:
                        logger.debug("sent to:")
                        for k, v in sent:
                            logger.debug(
                                f"object {k.get_id()} on rank {k.get_rank_id()}: {v}")

    @abc.abstractmethod
    def execute(self, phases, distributions, statistics, a_min_max):
        """Excecute balancing algorithm on Phase instance
            phases: list of Phase instances
            distributions: dictionary of load-varying variables
            statistics: dictionary of  statistics
            a_min_max: possibly empty list of optimal arrangements."""

        # Must be implemented by concrete subclass
        pass
