import abc
import os

from ..import PROJECT_PATH
from ..IO.lbsStatistics import compute_function_statistics
from ..Model.lbsRank import Rank
from ..Model.lbsPhase import Phase
from ..Model.lbsWorkModelBase import WorkModelBase
from ..Utils.lbsLogging import Logger

class AlgorithmBase:
    """An abstract base class of load/work balancing algorithms."""

    __metaclass__ = abc.ABCMeta

    _work_model: WorkModelBase
    _logger: Logger

    def __init__(self, work_model: WorkModelBase, parameters: dict, logger: Logger, rank_qoi: str, object_qoi: str):
        """Class constructor.

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        :param rank_qoi: rank QOI to track
        :param object_qoi: object QOI to track.
        """
        # Assert that a logger instance was passed
        if not isinstance(logger, Logger):
            self._logger.error(f"Incorrect type {type(logger)} passed instead of Logger instance")
            raise SystemExit(1)
        self._logger = logger

        # Assert that a work model base instance was passed
        if not isinstance(work_model, WorkModelBase):
            self._logger.error("Could not create an algorithm without a work model")
            raise SystemExit(1)
        self._work_model = work_model

        # Assert that a parameters dict was passed
        if not isinstance(parameters, dict):
            self._logger.error("Could not create an algorithm without a dictionary of parameters")
            raise SystemExit(1)

        # Assert that quantity of interest names are string
        if rank_qoi and not isinstance(rank_qoi, str):
            self._logger.error("Could not create an algorithm with non-string rank QOI name")
            raise SystemExit(1)
        self.__rank_qoi = rank_qoi
        if object_qoi and not isinstance(object_qoi, str):
            self._logger.error("Could not create an algorithm with non-string object QOI name")
            raise SystemExit(1)
        self.__object_qoi = object_qoi
        self._logger.info(
            f"Created base algorithm tracking rank {rank_qoi} and object {object_qoi}")

        # Initially no phase is assigned for processing
        self._rebalanced_phase = None

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
            ("ranks", lambda x: self._work_model.compute(x)): { #pylint:disable=W0108
                "minimum work": "minimum",
                "maximum work": "maximum",
                "total work": "sum",
                "work variance": "variance"}}

    def get_rebalanced_phase(self):
        """Return phased assigned for processing by algoritm."""
        return self._rebalanced_phase

    @staticmethod
    def factory(
        algorithm_name:str,
        parameters: dict,
        work_model: WorkModelBase,
        logger: Logger,
        rank_qoi: str,
        object_qoi:str):
        """Instantiate the necessary concrete algorithm."""
        # Load up available algorithms
        # pylint:disable=W0641:possibly-unused-variable,C0415:import-outside-toplevel
        from .lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
        from .lbsBruteForceAlgorithm import BruteForceAlgorithm
        from .lbsPhaseStepperAlgorithm import PhaseStepperAlgorithm
        from .lbsCentralizedPrefixOptimizerAlgorithm import CentralizedPrefixOptimizerAlgorithm
        # pylint:enable=W0641:possibly-unused-variable,C0415:import-outside-toplevel

        # Ensure that algorithm name is valid
        algorithm = locals()[algorithm_name + "Algorithm"]
        return algorithm(work_model, parameters, logger, rank_qoi, object_qoi)
        try:
            # Instantiate and return object
            algorithm = locals()[algorithm_name + "Algorithm"]
            return algorithm(work_model, parameters, logger, rank_qoi, object_qoi)
        except Exception as e:
            # Otherwise, error out
            logger.error(f"Could not create an algorithm with name {algorithm_name}")
            raise SystemExit(1) from e

    def _update_distributions_and_statistics(self, distributions: dict, statistics: dict):
        """Compute and update run distributions and statistics."""
        # Create or update distributions of object quantities of interest
        for object_qoi_name in tuple({"load", self.__object_qoi}):
            if not object_qoi_name:
                continue
            try:
                distributions.setdefault(f"object {object_qoi_name}", []).append(
                    {o.get_id(): getattr(o, f"get_{object_qoi_name}")()
                    for o in self._rebalanced_phase.get_objects()})
            except AttributeError as err:
                self.__print_QOI("obj")
                self._logger.error(f"Invalid object_qoi name \"{object_qoi_name}\"")
                raise SystemExit(1) from err

        # Create or update distributions of rank quantities of interest
        for rank_qoi_name in tuple({"objects", "load", self.__rank_qoi}):
            if not rank_qoi_name or rank_qoi_name == "work":
                continue
            try:
                distributions.setdefault(f"rank {rank_qoi_name}", []).append(
                    [getattr(p, f"get_{rank_qoi_name}")()
                    for p in self._rebalanced_phase.get_ranks()])
            except AttributeError as err:
                self.__print_QOI("rank")
                self._logger.error(f"Invalid rank_qoi name \"{rank_qoi_name}\"")
                raise SystemExit(1) from err
        distributions.setdefault("rank work", []).append(
            [self._work_model.compute(p) for p in self._rebalanced_phase.get_ranks()])

        # Create or update distributions of edge quantities of interest
        distributions.setdefault("sent", []).append(dict(
            self._rebalanced_phase.get_edge_maxima().items()))

        # Create or update statistics dictionary entries
        for (support, getter), stat_names in self.__statistics.items():
            for k, v in stat_names.items():
                stats = compute_function_statistics(
                    getattr(self._rebalanced_phase, f"get_{support}")(), getter)
                statistics.setdefault(k, []).append(getattr(stats, f"get_{v}")())

    def __print_QOI(self,rank_or_obj):
        """Print list of implemented QOI based on the '-verbosity' command line argument."""
        # Initialize file paths
        TARGET_DIR = os.path.join(PROJECT_PATH, "src", "lbaf", "Model")
        RANK_SCRIPT_NAME = "lbsRank.py"
        OBJECT_SCRIPT_NAME = "lbsObject.py"

        if rank_or_obj == "rank":
            # Create list of all Rank QOI (lbsRank.get_*)
            r_qoi_list = ["work"]
            lbsRank_file = open(os.path.join(TARGET_DIR, RANK_SCRIPT_NAME), 'r', encoding="utf-8")
            lbsRank_lines = lbsRank_file.readlines()
            for line in lbsRank_lines:
                if line[8:12] == "get_":
                    r_qoi_list.append(line[12:line.find("(")])

            # Print QOI based on verbosity level
            self._logger.error("List of all possible Rank QOI:")
            for r_qoi in r_qoi_list:
                self._logger.error("\t" + r_qoi)

        if rank_or_obj == "obj":
            # Create list of all Object QOI (lbsObject.get_*)
            o_qoi_list = []
            lbsObject_file = open(os.path.join(TARGET_DIR, OBJECT_SCRIPT_NAME), 'r', encoding="utf-8")
            lbsObject_lines = lbsObject_file.readlines()
            for line in lbsObject_lines:
                if line[8:12] == "get_":
                    o_qoi_list.append(line[12:line.find("(")])

            # Print QOI based on verbosity level
            self._logger.error("List of all possible Object QOI:")
            for o_qoi in o_qoi_list:
                self._logger.error("\t" + o_qoi)

    def _report_final_mapping(self, logger):
        """Report final rank object mapping in debug mode."""
        for rank in self._rebalanced_phase.get_ranks():
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

    def _initialize(self, p_id, phases, distributions, statistics):
        """Factor out pre-execution checks and initalizations."""
        # Ensure that a list with at least one phase was provided
        if not isinstance(phases, dict) or not all(
            [isinstance(p, Phase) for p in phases.values()]):
            self._logger.error("Algorithm execution requires a dictionary of phases")
            raise SystemExit(1)

        # Create a rebalanced phase to preserve phase to be rebalanced
        self._rebalanced_phase = Phase(self._logger, p_id)

        # Try to copy ranks from phase to be rebalanced to processd one
        try:
            new_ranks = []
            for r in phases[p_id].get_ranks():
                # Minimally instantiate rank and copy
                new_r = Rank(self._logger)
                new_r.copy(r)
                new_ranks.append(new_r)
            self._rebalanced_phase.set_ranks(new_ranks)
        except Exception as err:
            self._logger.error(f"No phase with index {p_id} is available for processing")
            raise SystemExit(1) from err
        self._logger.info(
            f"Processing phase {p_id} "
            f"with {self._rebalanced_phase.get_number_of_objects()} objects "
            f"across {self._rebalanced_phase.get_number_of_ranks()} ranks "
            f"into phase {self._rebalanced_phase.get_id()}")

        # Initialize run distributions and statistics
        self._update_distributions_and_statistics(distributions, statistics)

    @abc.abstractmethod
    def execute(self, p_id, phases, distributions, statistics, a_min_max):
        """Execute balancing algorithm on Phase instance.

        :param: p_id: index of phase to be rebalanced (all if equal to _)
        :param: phases: list of Phase instances
        :param: distributions: dictionary of load-varying variables
        :param: statistics: dictionary of  statistics
        :param: a_min_max: possibly empty list of optimal arrangements.
        """
