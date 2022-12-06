import abc
from logging import Logger
import sys

from ..IO.lbsStatistics import compute_function_statistics
from ..Model.lbsWorkModelBase import WorkModelBase
from ..Utils.exception_handler import exc_handler
from ..Utils.logger import logger


class AlgorithmBase:
    __metaclass__ = abc.ABCMeta
    """ An abstract base class of load/work balancing algorithms."""

    def __init__(self, work_model, parameters: dict, lgr: Logger, qoi_name: str=''):
        """ Class constructor:
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters
            qoi_name: optional additional QOI to track"""

        # Assign logger to instance variable
        self._logger = lgr

        # Assert that a work model base instance was passed
        if not isinstance(work_model, WorkModelBase):
            lgr.error("Could not create an algorithm without a work model")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.work_model = work_model

        # Assert that optional quantity of interest name is a string
        if qoi_name and not isinstance(qoi_name, str):
            lgr.error("Could not create an algorithm with non-string QOI name")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__qoi_name = qoi_name
        lgr.info(
            "Created base algorithm"
            + (f" tracking rank {qoi_name}" if qoi_name else ''))

        # Initially no phase is associated to algorithm
        self.phase = None

    @staticmethod
    def factory(algorithm_name:str, parameters: dict, work_model, lgr: Logger, qoi_name=''):
        """ Produce the necessary concrete algorithm."""

        # Load up available algorithms
        from .lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
        from .lbsBruteForceAlgorithm import BruteForceAlgorithm
        from .lbsPhaseStepperAlgorithm import PhaseStepperAlgorithm

        # Ensure that algorithm name is valid
        algorithm = locals()[algorithm_name + "Algorithm"]
        return algorithm(work_model, parameters, lgr, qoi_name)
        try:
            # Instantiate and return object
            algorithm = locals()[algorithm_name + "Algorithm"]
            return algorithm(work_model, parameters, lgr, qoi_name)
        except:
            # Otherwise, error out
            lgr.error(f"Could not create an algorithm with name {algorithm_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

    def update_distributions_and_statistics(self, distributions: dict, statistics: dict):
        """ Compute and update run distributions and statistics."""

        # Create or update distributions of rank quantities of interest
        for rank_qoi_name in ("objects", "load", self.__qoi_name):
            if not rank_qoi_name or rank_qoi_name == "work":
                continue
            distributions.setdefault(rank_qoi_name, []).append(
                [getattr(p, f"get_{rank_qoi_name}")()
                 for p in self.phase.get_ranks()])
        distributions.setdefault("work", []).append(
            [self.work_model.compute(p) for p in self.phase.get_ranks()])

        # Create or update distributions of edge quantities of interest
        distributions.setdefault("sent", []).append(
            {k: v for k, v in self.phase.get_edges().items()})
        
        # Compute load, volume, and work statistics
        _, l_min, _, l_max, l_var, _, _, l_imb = compute_function_statistics(
            self.phase.get_ranks(),
            lambda x: x.get_load())
        n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
            self.phase.get_edges().values(),
            lambda x: x)
        n_w, w_min, w_ave, w_max, w_var, _, _, _ = compute_function_statistics(
            self.phase.get_ranks(),
            lambda x: self.work_model.compute(x))

        # Create or update statistics dictionary entries
        statistics.setdefault("minimum load", []).append(l_min)
        statistics.setdefault("maximum load", []).append(l_max)
        statistics.setdefault("load variance", []).append(l_var)
        statistics.setdefault("load imbalance", []).append(l_imb)
        statistics.setdefault("number of communication edges", []).append(n_v)
        statistics.setdefault("maximum largest directed volume", []).append(v_max)
        statistics.setdefault("total largest directed volume", []).append(n_v * v_ave)
        statistics.setdefault("minimum work", []).append(w_min)
        statistics.setdefault("maximum work", []).append(w_max)
        statistics.setdefault("total work", []).append(n_w * w_ave)
        statistics.setdefault("work variance", []).append(w_var)

    def report_final_mapping(self, logger):
        """ Report final rank object mapping in debug mode."""

        for p in self.phase.get_ranks():
            logger.debug(f"Rank {p.get_id()}:")
            for o in p.get_objects():
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
        """ Excecute balancing algorithm on Phase instance
            phases: list of Phase instances
            distributions: dictionary of load-varying variables
            statistics: dictionary of  statistics
            a_min_max: possibly empty list of optimal arrangements"""

        # Must be implemented by concrete subclass
        pass
