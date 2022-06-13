from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import print_function_statistics


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
        if not phases or not isinstance(phases, list) or not all(
            [isinstance(p, Phase) for p in phases]):
            self.__logger.error(f"Algorithm execution requires a Phase instance")
            raise SystemExit(1)

        # Iterate over all phases
        for i, p in enumerate(phases):
            # Step through current phase
            self.__logger.info(f"Stepping through phase {i}")
            self.phase = p

            # Invalidate cache of edges
            self.phase.invalidate_edge_cache()

            # Compute and report iteration work statistics
            n_w, w_min, w_ave, w_max, w_var, _, _, _ = print_function_statistics(
                self.phase.get_ranks(),
                lambda x: self.work_model.compute(x),
                f"iteration {i + 1} rank works",
                self.__logger)

            # Update run distributions and statistics
            self.update_distributions_and_statistics(distributions, statistics)

            # Report current mapping in debug mode
            self.report_final_mapping(self.__logger)
