import os
import sys
import math
import itertools
import yaml
import csv
from logging import Logger

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.logger import logger


def get_objects(n_ranks: int, lgr: Logger, file_prefix: str, file_suffix: str) -> tuple:
    """ Read data from configuration and returns a tuple of objects with communication
    """

    # Instantiate data containers
    objects = []
    communication = {}

    # Instantiate data reader Class
    lr = LoadReader(file_prefix=file_prefix, logger=lgr, file_suffix=file_suffix)

    # Iterate over ranks, collecting objects and communication
    for rank in range(n_ranks):
        iter_map, comm = lr.read(node_id=rank)
        for rnk in iter_map.values():
            for obj in rnk.get_migratable_objects():
                objects.append({"id": obj.get_id(), "load": obj.get_load()})
        for obj_idx, obj_comm in comm.items():
            if obj_idx not in communication.keys():
                communication[obj_idx] = {"from": {}, "to": {}}
            if obj_comm.get("sent"):
                for snt in obj_comm.get("sent"):
                    communication[obj_idx]["to"].update({snt.get("to"): snt.get("bytes")})
            if obj_comm.get("received"):
                for rec in obj_comm.get("received"):
                    communication[obj_idx]["from"].update({rec.get("from"): rec.get("bytes")})

    # Sort objects for debugging purposes
    objects.sort(key=lambda x: x.get("id"))

    # Adding communication to objects
    for o in objects:
        idx = o.get("id")
        if communication.get(idx) is not None:
            o.update(communication.get(idx))

    # Return objects as tuple
    return tuple(objects)


def compute_load(objects: tuple, rank_object_ids: list) -> float:
    """ Return a load as a sum of all object loads
    """

    return sum([objects[i].get("load") for i in rank_object_ids])


def compute_volume(objects: tuple, rank_object_ids: list, direction: str) -> float:
    """ Return a volume of rank objects
    """

    # Initialize volume
    volume = 0.

    # Iterate over all rank objects
    for i in rank_object_ids:
        volume += sum([v for k, v in objects[i].get(direction, 0.).items() if k not in rank_object_ids])

    # Return computed volume
    return volume


def compute_arrangement_works(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float) -> dict:
    """ Return a dictionary with works of rank objects
    """

    # Build object rank map from arrangement
    ranks = {}
    for i, j in enumerate(arrangement):
        ranks.setdefault(j, []).append(i)

    # iterate over ranks
    works = {}
    for rank, rank_objects in ranks.items():
        # Compute per-rank loads
        works[rank] = alpha * compute_load(objects, rank_objects)

        # Compute communication volumes
        works[rank] += beta * max(compute_volume(objects, rank_objects, "from"),
                                  compute_volume(objects, rank_objects, "to"))

        # Add constant
        works[rank] += gamma

    # Return arrangement works
    return works


def compute_pairwise_reachable_arrangements(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float,
                                            w_max: float, from_id: int, to_id: int, n_ranks: int,
                                            max_objects: int = None):
    """ Compute arrangements reachable by moving up to a maximum number of objects from one rank to another
    """

    # Sanity checks regarding rank IDs
    if from_id >= n_ranks:
        LGR.error(f"Incorrect sender ID: {from_id} >= {n_ranks}")
        sys.excepthook = exc_handler
        raise SystemExit(1)
    if to_id >= n_ranks:
        LGR.error(f"Incorrect receiver ID: {to_id} >= {n_ranks}")
        sys.excepthook = exc_handler
        raise SystemExit(1)

    # Provide upper bounder on transfer size when none provided
    if not max_objects:
        max_objects = len(arrangement)

    # Search for all arrangement entries matching sender ID
    matches = [i for i, r in enumerate(arrangement) if r == from_id]

    # Loop over all allowable transfers to find reachable arrangements
    reachable = {}
    n_possible = 0
    for n in range(1, min(len(matches), max_objects) + 1):
        LGR.debug(f"Generating possible arrangements with {n} transfer(s) from rank {from_id} to rank {to_id}")
        # Iterate over all combinations with given size
        for c in itertools.combinations(matches, n):
            # Change all corresponding entries
            n_possible += 1
            new_arrangement = tuple(to_id if i in c else r for i, r in enumerate(arrangement))
            works = compute_arrangement_works(objects, new_arrangement, alpha, beta, gamma)

            # Check whether new arrangements is reachable
            w_max_new = max(works.values())
            if w_max_new <= w_max:
                reachable[new_arrangement] = w_max_new
    LGR.debug(f"Found {len(reachable)} reachable arrangement(s) from rank {from_id} to rank {to_id} amongst "
              f"{n_possible} possible one(s)")

    # Return dict of reachable arrangements
    return reachable


def compute_all_reachable_arrangements(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float,
                                       w_max: float, n_ranks: int, max_objects: int = None):
    """ Compute all arrangements reachable by moving up to a maximum number of objects
    """

    # Storage for all reachable arrangements with their maximum work
    reachable = {}

    # Loop over all possible senders
    for from_id in range(n_ranks):
        # Loop over all possible receivers
        for to_id in range(n_ranks):
            if from_id == to_id:
                continue
            reachable.update(compute_pairwise_reachable_arrangements(objects, arrangement, alpha, beta, gamma, w_max,
                                                                     from_id, to_id, n_ranks, max_objects))
    LGR.info(f"Found {len(reachable)} reachable arrangements, with maximum work: {max(reachable.values())}:")
    for k, v in reachable.items():
        LGR.info(f"\t{k}: {v}")

    # Return dict of reachable arrangements
    return reachable


def compute_min_max_arrangements_work(objects: tuple, alpha: float, beta: float, gamma: float, n_ranks: int):
    """ Compute all possible arrangements with repetition and minimax work
    """

    # Initialize quantities of interest
    n_arrangements = 0
    works_min_max = math.inf
    arrangements_min_max = []
    for arrangement in itertools.product(range(n_ranks), repeat=len(objects)):
        # Compute per-rank works for current arrangement
        works = compute_arrangement_works(objects, arrangement, alpha, beta, gamma)

        # Update minmax when relevant
        work_max = max(works.values())
        if work_max < works_min_max:
            works_min_max = work_max
            arrangements_min_max = [arrangement]
        elif work_max == works_min_max:
            arrangements_min_max.append(arrangement)

        # Keep track of number of arrangements for sanity
        n_arrangements += 1

    # Return quantities of interest
    return n_arrangements, works_min_max, arrangements_min_max


def recursively_compute_transitions(stack: list, visited: dict, objects: tuple, arrangement: tuple, alpha: float,
                                    beta: float, gamma: float, w_max: float, w_min_max: float, n_ranks: int,
                                    max_objects: int = None):
    """ Recursively compute all possible transitions to reachable arrangements from initial one
    """

    # Sanity checks regarding current arrangement
    w_a = visited.get(arrangement, -1.)
    if w_a < 0.:
        LGR.error(f"Arrangement {arrangement} not found in visited map")
        sys.excepthook = exc_handler
        raise SystemExit(1)

    # Append current arrangement to trajectory stack
    stack.append(arrangement)

    # Terminate recursion if global optimum was found
    if w_a == w_min_max:
        LGR.info(f"Global optimum found ({w_a}) for {arrangement}")
        for a in stack:
            LGR.info(f"\t{a} with maximum work {visited[a]}")
        return

    # Compute all reachable arrangements
    reachable = compute_all_reachable_arrangements(
        objects,
        arrangement,
        alpha, beta, gamma,
        w_max,
        n_ranks,
        max_objects)

    # Otherwise, iterate over all reachable arrangements
    for k, v in reachable.items():
        # Skip already visited arrangements
        if k in visited:
            continue

        # Add newly visited arrangements to map and recurse to it
        visited[k] = v
        recursively_compute_transitions(
            stack,
            visited,
            objects,
            k,
            alpha, beta, gamma,
            w_max, w_min_max,
            n_ranks,
            max_objects)

        # Pop last stack entry
        stack.pop()


if __name__ == '__main__':
    sys.setrecursionlimit(1500)

    def get_conf() -> dict:
        """ Gets config from file and returns a dictionary. """
        with open(os.path.join(project_path, "lbaf", "Applications", "conf.yaml"), 'rt') as conf_file:
            conf = yaml.safe_load(conf_file)
        return conf

    # Retrieve configuration
    CONF = get_conf()

    # Define number of ranks
    N_RANKS = CONF.get("x_ranks") * CONF.get("y_ranks") * CONF.get("z_ranks")

    # Define work constants
    ALPHA_G = CONF.get("work_model").get("parameters").get("alpha")
    BETA_G = CONF.get("work_model").get("parameters").get("beta")
    GAMMA_G = CONF.get("work_model").get("parameters").get("gamma")
    INPUT_DATA = os.path.join(project_path, CONF.get("log_file"))
    FILE_SUFFIX = CONF.get("file_suffix")
    LGR = logger()

    # Get objects from log files
    objects = get_objects(n_ranks=N_RANKS, lgr=LGR, file_prefix=INPUT_DATA, file_suffix=FILE_SUFFIX)

    # Print out input parameters
    LGR.info(f"alpha: {ALPHA_G}")
    LGR.info(f"beta: {BETA_G}")
    LGR.info(f"gamma: {GAMMA_G}")

    # Compute and report on best possible arrangements
    n_a, w_min_max, a_min_max = compute_min_max_arrangements_work(objects, alpha=ALPHA_G, beta=BETA_G, gamma=GAMMA_G,
                                                                  n_ranks=N_RANKS)
    if n_a != N_RANKS ** len(objects):
        LGR.error("Incorrect number of possible arrangements with repetition")
        sys.excepthook = exc_handler
        raise SystemExit(1)
    LGR.info(f"Number of generated arrangements with repetition: {n_a}")
    LGR.info(f"\tminimax work: {w_min_max:.4g} for {len(a_min_max)} optimal arrangements")

    # Write all optimal arrangements to CSV file
    output_dir = os.path.join(project_path, CONF.get("output_dir"))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    out_name = os.path.join(output_dir, "optimal-arrangements.csv")
    with open(out_name, 'w') as f:
        writer = csv.writer(f)
        for a in a_min_max:
            writer.writerow(a)
    LGR.info(f"Wrote {len(a_min_max)} optimal arrangement to {out_name}")

    # Start fom initial configuration
    initial_arrangement = (3, 0, 0, 0, 0, 1, 3, 3, 2)
    LGR.info(f"Initial arrangement: {initial_arrangement}")
    initial_works = compute_arrangement_works(objects, initial_arrangement, ALPHA_G, BETA_G, GAMMA_G)
    w_max = max(initial_works.values())
    visited = {initial_arrangement: w_max}
    LGR.info(f"\tper-rank works: {initial_works}")
    LGR.info(f"\tmaximum work: {w_max:.4g} average work: "
             f"{(sum(initial_works.values()) / len(initial_works)):.4g}")

    # Compute all possible reachable arrangements
    stack = []
    recursively_compute_transitions(
        stack,
        visited,
        objects,
        initial_arrangement,
        ALPHA_G, BETA_G, GAMMA_G,
        w_max, w_min_max,
        N_RANKS)

    # Report all optimal arrangements
    for k, v in visited.items():
        if v == w_min_max:
            LGR.info(f"Reachable optimal arrangement: {k}")
