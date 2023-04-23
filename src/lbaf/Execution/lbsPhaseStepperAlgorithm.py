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
        super(PhaseStepperAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

    def execute(self, _, phases: list, distributions: dict, statistics: dict, __):
        """ Execute brute force optimization algorithm on all phases."""

        # Ensure that a list with at least one phase was provided
        if not isinstance(phases, dict) or not all(
                [isinstance(p, Phase) for p in phases.values()]):
            self._logger.error(
                "Algorithm execution requires a dictionary of phases")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Iterate over all phases
        for p_id, self._processed_phase in phases.items():
            # Step through current phase
            self._logger.info(f"Stepping through phase {p_id}")

            # Compute and report phase rank work statistics
            print_function_statistics(
                self._processed_phase.get_ranks(),
                lambda x: self._work_model.compute(x),
                f"phase {p_id} rank works",
                self._logger)

            # Update run distributions and statistics
            self._update_distributions_and_statistics(
                distributions, statistics)

            # Report current mapping in debug mode
            self._report_final_mapping(self._logger)

        # Indicate that no phase was modified
        self._processed_phase = None
