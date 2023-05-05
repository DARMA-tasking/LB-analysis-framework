import os
import sys
import math
import itertools
import csv

import yaml

from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.logging import get_logger, Logger
from lbaf.Utils.common import project_path, abspath

def get_objects(n_ranks: int, logger: Logger, file_prefix: str, file_suffix: str = "json") -> tuple:
    """Read data from configuration and returns a tuple of objects with communication"""

    # Instantiate data containers
    objects = []
    communication = {}

    # Instantiate data reader Class
    reader = LoadReader(file_prefix=file_prefix, n_ranks=n_ranks, logger=logger, file_suffix=file_suffix)

    # Iterate over ranks, collecting objects and communication
    for rank in range(n_ranks):
        iter_map, comm = reader.read(node_id=rank)
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
    """Return a load as a sum of all object loads
    """

    return sum([objects[i].get("load") for i in rank_object_ids])


def compute_volume(objects: tuple, rank_object_ids: list, direction: str) -> float:
    """Return a volume of rank objects"""

    # Initialize volume
    volume = 0.

    # Iterate over all rank objects
    for i in rank_object_ids:
        volume += sum(v for (k, v) in objects[i].get(direction, []).items() if k not in rank_object_ids)

    # Return computed volume
    return volume


def compute_arrangement_works(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float) -> dict:
    """Return a dictionary with works of rank objects"""

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
    """Compute arrangements reachable by moving up to a maximum number of objects from one rank to another"""

    logger = get_logger()
    # Sanity checks regarding rank IDs
    if from_id >= n_ranks:
        logger.error(f"Incorrect sender ID: {from_id} >= {n_ranks}")
        sys.excepthook = exc_handler
        raise SystemExit(1)
    if to_id >= n_ranks:
        logger.error(f"Incorrect receiver ID: {to_id} >= {n_ranks}")
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
        logger.debug(f"Generating possible arrangements with {n} transfer(s) from rank {from_id} to rank {to_id}")
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
    logger.debug(f"Found {len(reachable)} reachable arrangement(s) from rank {from_id} to rank {to_id} amongst "
              f"{n_possible} possible one(s)")

    # Return dict of reachable arrangements
    return reachable


def compute_all_reachable_arrangements(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float,
                                       w_max: float, n_ranks: int, max_objects: int = None):
    """Compute all arrangements reachable by moving up to a maximum number of objects"""

    logger = get_logger()

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
    logger.info(f"Found {len(reachable)} reachable arrangements, with maximum work: {max(reachable.values())}:")
    for k, v in reachable.items():
        logger.info(f"\t{k}: {v}")

    # Return dict of reachable arrangements
    return reachable


def compute_min_max_arrangements_work(objects: tuple, alpha: float, beta: float, gamma: float, n_ranks: int):
    """Compute all possible arrangements with repetition and minimax work"""

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
    """Recursively compute all possible transitions to reachable arrangements from initial one"""

    logger = get_logger()

    # Sanity checks regarding current arrangement
    w_a = visited.get(arrangement, -1.)
    if w_a < 0.:
        logger.error(f"Arrangement {arrangement} not found in visited map")
        sys.excepthook = exc_handler
        raise SystemExit(1)

    # Append current arrangement to trajectory stack
    stack.append(arrangement)

    # Terminate recursion if global optimum was found
    if w_a == w_min_max:
        logger.info(f"Global optimum found ({w_a}) for {arrangement}")
        for a in stack:
            logger.info(f"\t{a} with maximum work {visited[a]}")
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


def main():
    """Main implementation"""
    sys.setrecursionlimit(1500)
    root_logger = get_logger()

    def get_conf() -> dict:
        """Gets config from file and returns a dictionary."""

        with open(os.path.join(project_path(), "config", "conf.yaml"), "rt", encoding="utf-8") as conf_file:
            conf = yaml.safe_load(conf_file)
        return conf

    # Retrieve configuration
    conf = get_conf()
    conf_dir = os.path.join(project_path(), "config")

    # Define number of ranks
    viz = conf.get("LBAF_Viz")
    n_ranks = viz.get("x_ranks") * viz.get("y_ranks") * viz.get("z_ranks")

    # Define work constants
    alpha_g = conf.get("work_model").get("parameters").get("alpha")
    beta_g = conf.get("work_model").get("parameters").get("beta")
    gamma_g = conf.get("work_model").get("parameters").get("gamma")
    file_suffix = conf.get("file_suffix", "json")

    # Get datastem as absolute prefix
    data_stem = conf.get("from_data").get("data_stem")
    data_dir = f"{os.sep}".join(data_stem.split(os.sep)[:-1])
    file_prefix = data_stem.split(os.sep)[-1]

    data_dir = abspath(data_dir, conf_dir) # make absolute path
    file_prefix = f"{os.sep}".join([data_dir, file_prefix]) # make absolute path prefix

    # Get objects from log files
    objects = get_objects(n_ranks=n_ranks, logger=root_logger, file_prefix=file_prefix, file_suffix=file_suffix)

    # Print out input parameters
    root_logger.info(f"alpha: {alpha_g}")
    root_logger.info(f"beta: {beta_g}")
    root_logger.info(f"gamma: {gamma_g}")

    # Compute and report on best possible arrangements
    n_a, w_min_max, a_min_max = compute_min_max_arrangements_work(objects, alpha=alpha_g, beta=beta_g, gamma=gamma_g,
                                                                  n_ranks=n_ranks)
    if n_a != n_ranks ** len(objects):
        root_logger.error("Incorrect number of possible arrangements with repetition")
        sys.excepthook = exc_handler
        raise SystemExit(1)
    root_logger.info(f"Number of generated arrangements with repetition: {n_a}")
    root_logger.info(f"\tminimax work: {w_min_max:.4g} for {len(a_min_max)} optimal arrangements")

    # Write all optimal arrangements to CSV file
    output_dir = abspath(conf.get("output_dir"), relative_to=conf_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    out_name = os.path.join(output_dir, "optimal-arrangements.csv")
    with open(out_name, "w", encoding="utf-8") as input_file:
        writer = csv.writer(input_file)
        for a in a_min_max:
            writer.writerow(a)
    root_logger.info(f"Wrote {len(a_min_max)} optimal arrangement to {out_name}")

    # Start fom initial configuration
    initial_arrangement = (3, 0, 0, 0, 0, 1, 3, 3, 2)
    root_logger.info(f"Initial arrangement: {initial_arrangement}")
    initial_works = compute_arrangement_works(objects, initial_arrangement, alpha_g, beta_g, gamma_g)
    w_max = max(initial_works.values())
    visited = {initial_arrangement: w_max}
    root_logger.info(f"\tper-rank works: {initial_works}")
    root_logger.info(f"\tmaximum work: {w_max:.4g} average work: "
             f"{(sum(initial_works.values()) / len(initial_works)):.4g}")

    # Compute all possible reachable arrangements
    stack1 = []
    recursively_compute_transitions(
        stack1,
        visited,
        objects,
        initial_arrangement,
        alpha_g, beta_g, gamma_g,
        w_max, w_min_max,
        n_ranks)

    # Report all optimal arrangements
    for k, v in visited.items():
        if v == w_min_max:
            root_logger.info(f"Reachable optimal arrangement: {k}")

if __name__ == '__main__':
    main()
