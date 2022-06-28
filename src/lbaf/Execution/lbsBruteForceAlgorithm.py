import sys
import math
import itertools
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsPhase import Phase
from ..Utils.exception_handler import exc_handler


class BruteForceAlgorithm(AlgorithmBase):
    """ A concrete class for the brute force optimization algorithm
    """

    def __init__(self, work_model, parameters, lgr: Logger):
        """ Class constructor
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters
        """

        # Call superclass init
        super(BruteForceAlgorithm, self).__init__(work_model, parameters)

        # Assign logger to instance variable
        self.__logger = lgr

        # Assign optional parameters
        self.__skip_transfer = parameters.get("skip_transfer", False)
        
        self.__logger.info(f"Instantiated {'with' if self.__skip_transfer else 'without'} transfer stage skipping")

    def compute_arrangement_works(self, objects: tuple, arrangement: tuple) -> dict:
        """ Return a dictionary with works of rank objects
        """

        # Build object rank map from arrangement
        ranks = {}
        for i, j in enumerate(arrangement):
            ranks.setdefault(j, []).append(i)

        # iterate over ranks
        works = {}
        for rank, rank_object_ids in ranks.items():
            # Compute load component for current rank
            values = {
                "load": sum([objects[i].get("time") for i in rank_object_ids])}
            
            # Compute received communication volume
            v = 0.0
            for i in rank_object_ids:
                v += sum([v for k, v in objects[i].get("from", 0.).items() if k not in rank_object_ids])
            values["received volume"] = v

            # Compute sent communication volume
            v = 0.0
            for i in rank_object_ids:
                v += sum([v for k, v in objects[i].get("to", 0.).items() if k not in rank_object_ids])
            values["sent volume"] = v

            # Aggregate and store work for this rank
            works[rank] = self.work_model.aggregate(values)

        # Return arrangement works
        return works

    def execute(self, phases: list, distributions: dict, statistics: dict, _):
        """ Execute brute force optimization algorithm on Phase instance
        """
        # Ensure that a list with at least one phase was provided
        if not phases or not isinstance(phases, list) or not isinstance(
                (phase := phases[0]), Phase):
            self.__logger.error(f"Algorithm execution requires a Phase instance")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.phase = phase

        # Initialize run distributions and statistics
        self.update_distributions_and_statistics(distributions, statistics)

        # Prepare input data for rank order enumerator
        self.__logger.info(f"Starting brute force optimization")
        objects = []

        # Iterate over ranks
        phase_ranks = phase.get_ranks()
        for rank in phase_ranks:
            for o in rank.get_objects():
                entry = {
                    "id": o.get_id(),
                    "rank": rank,
                    "time": o.get_time(),
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
            self.__logger.error("No optimal arrangements were found")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        if n_arrangements != n_ranks ** len(objects):
            self.__logger.error("Incorrect number of possible arrangements with repetition")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self.__logger.info(f"Minimax work: {w_min_max:.4g} for {len(a_min_max)} optimal arrangements amongst {n_arrangements}")

        # Skip object transfers when requested
        if self.__skip_transfer:
            self.__logger.info("Skipping object transfers")
            return

        # Pick first optimal arrangement and reassign objects accordingly
        n_transfers = 0
        arrangement = a_min_max[0]
        self.__logger.debug(f"Reassigning objects with arrangement {arrangement}")
        for i, a in enumerate(arrangement):
            # Skip objects that do not need transfer
            p_src = objects[i]["rank"]
            p_dst = phase_ranks[a]
            if p_src == p_dst:
                continue

            # Otherwise locate object on source and transfer to destination
            object_id = objects[i]["id"]
            for o in p_src.get_objects():
                if o.get_id() == object_id:
                    self.__logger.debug(f"transferring object {o.get_id()} ({o.get_time()}) to rank {p_dst.get_id()}")
                    p_src.remove_migratable_object(o, p_dst)
                    p_dst.add_migratable_object(o)
                    o.set_rank_id(p_dst.get_id())
                    n_transfers += 1

        # Report on object transfers
        self.__logger.info(f"{n_transfers} transfers occurred")

        # Invalidate cache of edges
        self.phase.invalidate_edge_cache()

        # Update run distributions and statistics
        self.update_distributions_and_statistics(distributions, statistics)

        # Report final mapping in debug mode
        self.report_final_mapping(self.__logger)
