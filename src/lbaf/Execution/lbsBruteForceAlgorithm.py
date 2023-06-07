"""lbsBruteForceAlgorithm module.
Exports: BruteForceAlgorithm class"""
import sys
import math
import itertools
from logging import Logger

from ..Model.lbsAffineCombinationWorkModel import AffineCombinationWorkModel
from .lbsAlgorithmBase import AlgorithmBase
from ..Utils.exception_handler import exc_handler
from ..IO.lbsStatistics import compute_arrangement_works


class BruteForceAlgorithm(AlgorithmBase):
    """A concrete class for the brute force optimization algorithm"""

    def __init__(self, work_model, parameters: dict, lgr: Logger, rank_qoi: str, object_qoi: str):
        """Class constructor
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters
            rank_qoi: rank QOI to track
            object_qoi: object QOI to track."""

        # Call superclass init
        super(BruteForceAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Assign optional parameters
        self.__skip_transfer = parameters.get("skip_transfer", False)
        self._logger.info(f"Instantiated {'with' if self.__skip_transfer else 'without'} transfer stage skipping")

    def compute_arrangement_works(self, objects: tuple, arrangement: tuple) -> dict:
        """Return a dictionary with works of rank objects."""

        ranks = {}
        for i, j in enumerate(arrangement):
            ranks.setdefault(j, []).append(i)

        affine_combination = isinstance(self._work_model, AffineCombinationWorkModel)
        alpha = self._work_model.get_alpha() if affine_combination else 1
        beta = self._work_model.get_beta() if affine_combination else 0
        gamma = self._work_model.get_gamma() if affine_combination else 0
        return compute_arrangement_works(objects, arrangement, alpha, beta, gamma)

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, _):
        """ Execute brute force optimization algorithm on phase with index p_id."""

        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, distributions, statistics)

        # Prepare input data for rank order enumerator
        self._logger.info("Starting brute force optimization")
        objects = []

        initial_phase = phases[min(phases.keys())]
        phase_ranks = initial_phase.get_ranks()
        objects = initial_phase.get_objects()

        # Initialize quantities of interest
        n_arrangements = 0
        w_min_max = math.inf
        a_min_max = []
        n_ranks = len(phase_ranks)

        # Compute all possible arrangements with repetition and minimax work
        for arrangement in itertools.product(range(n_ranks), repeat=len(objects)):
            # Compute per-rank works for current arrangement
            works = self.compute_arrangement_works(objects, arrangement)

            # Update minmax when relevant
            work_max = max(works.values())
            if work_max < w_min_max:
                w_min_max = work_max
                a_min_max = [arrangement]
            elif work_max == w_min_max:
                a_min_max.append(arrangement)

            # Keep track of number of arrangements for sanity
            n_arrangements += 1

        # Sanity checks
        if not a_min_max:
            self._logger.error("No optimal arrangements were found")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        if n_arrangements != n_ranks ** len(objects):
            self._logger.error(
                "Incorrect number of possible arrangements with repetition")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._logger.info(
            f"Minimax work: {w_min_max:.4g} for {len(a_min_max)} optimal arrangements amongst {n_arrangements}")

        # Skip object transfers when requested
        if self.__skip_transfer:
            self._logger.info("Skipping object transfers")
            return

        # Pick first optimal arrangement and reassign objects accordingly
        n_transfers = 0
        arrangement = a_min_max[0]
        self._logger.debug(f"Reassigning objects with arrangement {arrangement}")
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
