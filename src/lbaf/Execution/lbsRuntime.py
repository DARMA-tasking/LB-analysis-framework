import sys
import math
from logging import Logger

from ..Model.lbsPhase import Phase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsWorkModelBase import WorkModelBase
from ..Execution.lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import print_function_statistics, compute_function_statistics, min_Hamming_distance


class Runtime:
    """ A class to handle the execution of the LBS
    """
    def __init__(self, phase: Phase, w: dict, b: dict, o_s: str, a: list, brute_force_optimization: bool, logger: Logger = None):
        """ Class constructor:
            phase: phase instance
            w: dictionary with work model name and optional parameters
            b: dictionary with balancing algorithm and optional parameters
            o_s: name of object ordering strategy
            a: arrangements that minimize maximum work
            logger: logger for output messages
        """

        # Keep track of list of arrangements with minimax work
        self.__a_min_max = a if brute_force_optimization else None

        # Assign logger to instance variable
        self.__logger = logger

        # If no LBS phase was provided, do not do anything
        if not isinstance(phase, Phase):
            self.__logger.warning("Could not create a LBS runtime without a phase")
            return
        else:
            self.__phase = phase

        # Instantiate work model
        self.__work_model = WorkModelBase.factory(w.get("name"), w.get("parameters", {}), lgr=self.__logger)
        if not self.__work_model:
            self.__logger.error(f"Could not instantiate a work model of type {self.__work_model}")
            sys.exit(1)

        # Instantiate balancing algorithm
        self.__algorithm = AlgorithmBase.factory(
            b.get("name"),
            self.__work_model,
            b.get("parameters", {}),
            lgr=self.__logger)
        if not self.__algorithm:
            self.__logger.error(f"Could not instantiate an algorithm of type {self.__algorithm}")
            sys.exit(1)

        # Initialize load, sent, and work distributions
        self.distributions = {
            "load": [[p.get_load() for p in self.__phase.get_ranks()]],
            "sent": [{k: v for k, v in self.__phase.get_edges().items()}],
            "work": [[self.__work_model.compute(p) for p in self.__phase.get_ranks()]]}

        # Compute global load, volume and work statistics
        _, l_min, self.average_load, l_max, l_var, _, _, l_imb = compute_function_statistics(
            self.__phase.get_ranks(),
            lambda x: x.get_load())
        n_v, _, v_ave, v_max, _, _, _, _ = compute_function_statistics(
            self.__phase.get_edges().values(),
            lambda x: x)
        n_w, w_min, w_ave, w_max, w_var, _, _, _ = compute_function_statistics(
            self.__phase.get_ranks(),
            lambda x: self.__work_model.compute(x))

        # Compute initial arrangement and report minimum Hamming distance
        arrangement = tuple(
            v for _, v in sorted({
                o.get_id(): p.get_id()
                for p in self.__phase.get_ranks() for o in p.get_objects()
                }.items()))
        if brute_force_optimization:
            hd_min = min_Hamming_distance(arrangement, self.__a_min_max)
            self.__logger.info(f"Iteration 0 minimum Hamming distance to optimal arrangements: {hd_min}")
        else:
            hd_min = math.nan
        self.__logger.debug(f"Iteration 0 arrangement: {arrangement}")

        # Initialize run statistics
        self.statistics = {
            "minimum load": [l_min],
            "maximum load": [l_max],
            "load variance": [l_var],
            "load imbalance": [l_imb],
            "number of communication edges": [n_v],
            "maximum largest directed volume": [v_max],
            "total largest directed volume": [n_v * v_ave],
            "minimum work": [w_min],
            "maximum work": [w_max],
            "total work": [n_w * w_ave],
            "work variance": [w_var],
            "minimum Hamming distance to optimum": [hd_min]}


    def execute(self, n_iterations, n_rounds, f, max_n_objects, deterministic_transfer):
        """ Launch runtime execution
            n_iterations: integer number of load-balancing iterations
            n_rounds: integer number of gossiping rounds
            f: integer fanout
            max_n_objects: maximum number of objects transferred at once
            deterministic_transfer: deterministic or probabilistic transfer
        """

        # Report on initial per-rank work
        print_function_statistics(
            self.__phase.get_ranks(),
            lambda x: self.__work_model.compute(x),
            "initial rank works",
            logger=self.__logger)

        # Execute balancing algorithm
        self.__algorithm.execute(
            self.__phase,
            self.distributions,
            self.statistics,
            self.average_load,
            self.__a_min_max)


