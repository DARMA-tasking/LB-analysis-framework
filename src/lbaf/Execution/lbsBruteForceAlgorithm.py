"""lbsBruteForceAlgorithm"""
from logging import Logger

from ..Model.lbsAffineCombinationWorkModel import AffineCombinationWorkModel
from .lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import compute_min_max_arrangements_work


class BruteForceAlgorithm(AlgorithmBase):
    """A concrete class for the brute force optimization algorithm"""

    def __init__(self, work_model, parameters: dict, lgr: Logger, rank_qoi: str, object_qoi: str):
        """Class constructor.

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        :param rank_qoi: rank QOI to track
        :param object_qoi: object QOI to track.
        """
        # Call superclass init
        super(BruteForceAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Assign optional parameters
        self.__skip_transfer = parameters.get("skip_transfer", False)
        self._logger.info(
            f"Instantiated {'with' if self.__skip_transfer else 'without'} transfer stage skipping")

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, _):
        """Execute brute force optimization algorithm on phase with index p_id."""
        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, distributions, statistics)
        self._logger.info("Starting brute force optimization")
        initial_phase = phases[min(phases.keys())]
        phase_ranks = initial_phase.get_ranks()
        objects = initial_phase.get_objects()
        n_ranks = len(phase_ranks)
        affine_combination = isinstance(
            self._work_model, AffineCombinationWorkModel)
        alpha, beta, gamma = [
            self._work_model.get_alpha() if affine_combination else 1.0,
            self._work_model.get_beta() if affine_combination else 0.0,
            self._work_model.get_gamma() if affine_combination else 0.0]
        _n_a, _w_min_max, a_min_max = compute_min_max_arrangements_work(objects, alpha, beta, gamma, n_ranks,
                                                                        logger=self._logger)

        # Skip object transfers when requested
        if self.__skip_transfer:
            self._logger.info("Skipping object transfers")
            return

        # Pick first optimal arrangement and reassign objects accordingly
        n_transfers = 0
        arrangement = a_min_max[0]
        self._logger.debug(
            f"Reassigning objects with arrangement {arrangement}")
        for i, a in enumerate(arrangement):
            # Skip objects that do not need transfer
            r_src = phase_ranks[objects[i].get_rank_id()]
            r_dst = phase_ranks[a]
            if r_src == r_dst:
                continue

            # Otherwise locate object on source and transfer to destination
            object_id = objects[i].get_id()
            for o in r_src.get_objects():
                if o.get_id() == object_id:
                    # Perform transfer
                    self._rebalanced_phase.transfer_object(r_src, o, r_dst)
                    n_transfers += 1

        # Report on object transfers
        self._logger.info(f"{n_transfers} transfers occurred")

        # Update run distributions and statistics
        self._update_distributions_and_statistics(distributions, statistics)

        # Report final mapping in debug mode
        self._report_final_mapping(self._logger)
