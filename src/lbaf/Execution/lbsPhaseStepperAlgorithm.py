import sys
import math
import itertools
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsPhase import Phase


class PhaseStepperAlgorithm(AlgorithmBase):
    """ A concrete class for the phase stepper non-optimzing algorithm
    """

    def __init__(self, work_model, parameters, lgr: Logger):
        """ Class constructor
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters
        """

        # Call superclass init
        super(PhaseStepperAlgorithm, self).__init__(work_model, parameters)

        # Assign logger to instance variable
        self.__logger = lgr

    def execute(self, phases: list, distributions: dict, statistics: dict, _):
        """ Execute brute force optimization algorithm on Phase instance
        """

        # Ensure that a list with at least one phase was provided
        if not phases or not isinstance(phases, list) or not isinstance(
            (phase := phases[0]), Phase):
            self.__logger.error(f"Algorithm execution requires a Phase instance")
            raise SystemExit(1)
        self.phase = phase

        # Initialize run distributions and statistics
        self.update_distributions_and_statistics(distributions, statistics)

        # Prepare input data for rank order enumerator
        self.__logger.info(f"Starting phase stepping")
        objects = []

        # Invalidate cache of edges
        self.phase.invalidate_edge_cache()

        # Update run distributions and statistics
        self.update_distributions_and_statistics(distributions, statistics)

        # Report final mapping in debug mode
        self.report_final_mapping(self.__logger)
