import sys
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import print_function_statistics
from ..Utils.exception_handler import exc_handler


class PhaseStepperAlgorithm(AlgorithmBase):
    """ A concrete class for the phase stepper non-optimzing algorithm."""

    def __init__(self, work_model, parameters: dict, lgr: Logger, rank_qoi: str, object_qoi: str):
        """ Class constructor
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters
            rank_qoi: rank QOI to track
            object_qoi: object QOI to track."""

        # Call superclass init
        super(InformAndTransferAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

    def execute(self, phases: list, distributions: dict, statistics: dict, _):
        """ Execute brute force optimization algorithm on Phase instance."""

        # Ensure that a list with at least one phase was provided
        if not phases or not isinstance(phases, list) or not all(
                [isinstance(p, Phase) for p in phases]):
            self._logger.error(f"Algorithm execution requires a Phase instance")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Iterate over all phases
        for i, p in enumerate(phases):
            # Step through current phase
            self._logger.info(f"Stepping through phase {i}")
            self._phase = p

            # Compute and report iteration work statistics
            print_function_statistics(
                self._phase.get_ranks(),
                lambda x: self._work_model.compute(x),
                f"iteration {i + 1} rank works",
                self._logger)

            # Update run distributions and statistics
            self.update_distributions_and_statistics(
                distributions, statistics)

            # Report current mapping in debug mode
            self.report_final_mapping(self._logger)
