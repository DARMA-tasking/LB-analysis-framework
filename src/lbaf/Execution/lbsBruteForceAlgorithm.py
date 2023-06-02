import sys
import math
import itertools
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsPhase import Phase
from ..Utils.exception_handler import exc_handler


class BruteForceAlgorithm(AlgorithmBase):
    """A concrete class for the brute force optimization algorithm
    """

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

        # Build object rank map from arrangement
        ranks = {}
        for i, j in enumerate(arrangement):
            ranks.setdefault(j, []).append(i)

        # iterate over ranks
        works = {}
        for rank, rank_object_ids in ranks.items():
            # Compute load component for current rank
            values = {
                "load":
                sum([objects[i].get("load") for i in rank_object_ids])}

            # Compute received communication volume
            v = 0.0
            for i in rank_object_ids:
                v += sum([
                    v for k, v in objects[i].get("from", 0.).items()
                    if k not in rank_object_ids])
            values["received volume"] = v

            # Compute sent communication volume
            v = 0.0
            for i in rank_object_ids:
                v += sum([
                    v for k, v in objects[i].get("to", 0.).items()
                    if k not in rank_object_ids])
            values["sent volume"] = v

            # Aggregate and store work for this rank
            works[rank] = self._work_model.aggregate(values)

        # Return arrangement works
        return works

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, _):
        """ Execute brute force optimization algorithm on phase with index p_id."""
        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, distributions, statistics)

        # Prepare input data for rank order enumerator
        self._logger.info("Starting brute force optimization")
        objects = []

        # Iterate over ranks
        phase_ranks = Phase.get_ranks()
        for rank in phase_ranks:
            for o in rank.get_objects():
                entry = {
                    "id": o.get_id(),
                    "rank": rank,
                    "load": o.get_load(),
                    "to": {},
                    "from": {}}
                comm = o.get_communicator()
                if comm:
                    for k, v in comm.get_sent().items():
                        entry["to"][k.get_id()] = v
                    for k, v in comm.get_received().items():
                        entry["from"][k.get_id()] = v
                objects.append(entry)
        objects.sort(key=lambda x: x.get("id"))

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
        if not len(a_min_max):
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
            r_src = objects[i]["rank"]
            r_dst = phase_ranks[a]
            if r_src == r_dst:
                continue

            # Otherwise locate object on source and transfer to destination
            object_id = objects[i]["id"]
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
