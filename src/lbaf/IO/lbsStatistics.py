"""lbsStatistics"""
import itertools
import math
import random as rnd
from logging import Logger
from typing import Optional

from numpy import random


class Statistics:
    """A class storing descriptive statistics."""

    def __init__(
        self,
        n: int,
        mini: float,
        mean: float,
        maxi: float,
        var: float,
        g1: float,
        g2: float):
        """Class constructor given descriptive statistics values."""
        # Store primary statistics
        self.primary_statistics = {
            "cardinality": n,
            "minimum": mini,
            "average": mean,
            "maximum": maxi,
            "variance": var,
            "skewness": g1,
            "kurtosis": g2}

        # Compute and store derived statistics
        self.derived_statistics = {
            "sum": n * mean,
            "imbalance":  maxi / mean - 1.0 if mean > 0.0 else math.nan,
            "standard deviation": math.sqrt(var),
            "kurtosis excess": g2 - 3.0}

        # Merge all statistics
        self.statistics = {
            **self.primary_statistics, **self.derived_statistics}

        # Define getter methods
        def __getter_factory(k):
            def getter():
                return self.statistics[k]
            return getter
        for k in self.statistics:
            setattr(self, f"get_{k.replace(' ', '_')}", __getter_factory(k))


def initialize():
    """Seed pseudo-random number generators."""
    rnd.seed(146)
    random.seed(146)


def error_out(distribution_name, parameters, logger: Logger):
    """Logs an error indicating not enough parameters for a distribution."""
    logger.error(f"not enough parameters in {parameters} for {distribution_name} distribution.")
    return None


def sampler(distribution_name, parameters, logger: Logger):
    """Return a pseudo-random number generator based of requested type."""
    # Uniform U(a,b) distribution
    if distribution_name.lower() == "uniform":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters, logger=logger)

        # Return uniform distribution over given interval
        return lambda: rnd.uniform(*parameters), f"U[{parameters[0]};{parameters[1]}]"

    # Binomial B(n,p) distribution
    elif distribution_name.lower() == "binomial":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters, logger=logger)

        # Return binomial distribution with given number of Bernoulli trials
        return lambda: random.binomial(*parameters), f"B[{parameters[0]};{parameters[1]}]"

    # Log-normal distribution with given mean and variance
    elif distribution_name.lower() == "lognormal":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters, logger=logger)

        # Determine parameters of log-normal distribution
        m2 = parameters[0] * parameters[0]
        v = parameters[1]
        r = math.sqrt(m2 + v)
        if r == 0:
            logger.error(f"r={r} should not be zero.")
            return None, None
        mu = math.log(m2 / r)
        sigma = math.sqrt(math.log(r * r / m2))

        # Return log-normal distribution with given mean and variance
        return lambda: rnd.lognormvariate(mu, sigma), f"LogN({mu:.6g};{sigma:.6g})"

    # Unsupported distribution type
    else:
        logger.error(f"{distribution_name} distribution is not supported.")
        return None, None


def Hamming_distance(arrangement_1, arrangement_2):
    """Compute Hamming distance between two arrangements.""" # pylint:disable=C0103:invalid-name
    # Distance can only be compute between same length arrangements
    if len(arrangement_1) != len(arrangement_2):
        return math.inf

    # Iterate over arrangement values
    hd = 0
    for i, j in zip(arrangement_1, arrangement_2):
        # Increment distance for each pair of different entries
        if i != j:
            hd += 1

    # Return the final count of differences
    return hd


def min_Hamming_distance(arrangement, arrangement_list):
    """Compute minimum Hamming distance from arrangement to list of arrangements.""" # pylint:disable=C0103:invalid-name
    # Minimum distance is at least equal to arrangement length
    hd_min = len(arrangement)

    # Iterate over list of arrangements
    for a in arrangement_list:
        # Compute distance and update minimum as needed
        hd = Hamming_distance(arrangement, a)
        if hd < hd_min:
            hd_min = hd

    # Return minimum distance
    return hd_min


def inverse_transform_sample(cmf):
    """Sample from distribution defined by cumulative mass function
    This is a.k.a. the Smirnov transform.
    """
    # Generate number from pseudo-random distribution U([0;1])
    u = rnd.random()

    # Look for when u is first encountered in CMF
    for k, v in cmf.items():
        if not v < u:
            # Return sample point
            return k


def compute_volume(objects: tuple, rank_object_ids: list, direction: str) -> float:
    """Return a volume of rank objects"""
    # Initialize volume
    volume = 0.

    # Iterate over all rank objects
    for _ in rank_object_ids:
        volume += sum(v for (k, v) in getattr(objects[0], direction, {}).items() if k not in rank_object_ids)

    # Return computed volume
    return volume


def compute_load(objects: tuple, rank_object_ids: list) -> float:
    """Return a load as a sum of all object loads."""
    return sum([objects[i].get_load() for i in rank_object_ids])


def compute_arrangement_works(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float) -> dict:
    """Return a dictionary with works of rank objects."""
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
        if beta != 0.0: # do not calculate max if beta = 0 for better performance
            works[rank] += beta * max(compute_volume(objects, rank_objects, "received"),
                                    compute_volume(objects, rank_objects, "sent"))

        # Add constant
        works[rank] += gamma

    # Return arrangement works
    return works


def compute_min_max_arrangements_work(objects: tuple, alpha: float, beta: float, gamma: float, n_ranks: int,
    sanity_checks=True, logger: Optional[Logger] = None):
    """Compute all possible arrangements with repetition and minimax work."""
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

    # Sanity checks
    if sanity_checks:
        if not arrangements_min_max:
            if logger is not None:
                logger.error("No optimal arrangements were found")
            raise SystemExit(1)
        if n_arrangements != n_ranks ** len(objects):
            if logger is not None:
                logger.error("Incorrect number of possible arrangements with repetition")
            raise SystemExit(1)
        if logger is not None:
            logger.info(
                f"Minimax work: {works_min_max:.4g} for {len(arrangements_min_max)} optimal arrangements"
                " amongst {n_arrangements}")

    # Return quantities of interest
    return n_arrangements, works_min_max, arrangements_min_max


def compute_pairwise_reachable_arrangements(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float,
                                            w_max: float, from_id: int, to_id: int, n_ranks: int,
                                            max_objects: Optional[int] = None, logger: Optional[Logger] = None):
    """Compute arrangements reachable by moving up to a maximum number of objects from one rank to another."""
    # Sanity checks regarding rank IDs
    if from_id >= n_ranks:
        if logger is not None:
            logger.error(f"Incorrect sender ID: {from_id} >= {n_ranks}")
        raise SystemExit(1)
    if to_id >= n_ranks:
        if logger is not None:
            logger.error(f"Incorrect receiver ID: {to_id} >= {n_ranks}")
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
        if logger is not None:
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
    if logger is not None:
        logger.debug(f"Found {len(reachable)} reachable arrangement(s) from rank {from_id} to rank {to_id} amongst "
                    f"{n_possible} possible one(s)")

    # Return dict of reachable arrangements
    return reachable


def compute_function_statistics(population, fct) -> Statistics:
    """Compute descriptive statistics of a function over a population."""
    # Bail out early if population is empty
    if not population:
        return Statistics(0, math.nan, math.nan, math.nan, math.nan, math.nan, math.nan)

    # Initialize statistics
    n = 0
    f_min = math.inf
    f_max = -math.inf
    f_ave = 0.
    f_ag2 = 0.
    f_ag3 = 0.
    f_ag4 = 0.

    # Stream population and to compute function statistics
    has_inf_values = False
    for x in population:
        # Compute image by function
        y = fct(x)

        # Update cardinality
        n += 1

        # Update minimum
        if y < f_min:
            f_min = y

        # Update maximum
        if y > f_max:
            f_max = y

        # Handle infinite values and break out early
        if y in (-math.inf, math.inf):
            has_inf_values = True
            if f_ave == -float(y):
                f_ave = math.nan
            else:
                f_ave = math.inf
            f_ag2, f_ag3, f_ag4 = math.nan, math.nan, math.nan

        # Skip further calculations if infinite values encountered
        if has_inf_values:
            continue

        # Compute difference to mean and its inverse
        d = y - f_ave
        A = d / n

        # Update mean and difference to updated mean
        f_ave += A
        B = y - f_ave

        # Update aggregates in this order as previous values required
        r = n - 1
        f_ag4 += A * (A * A * d * r * (n * (n - 3) + 3) + 6 * A * f_ag2 - 4 * f_ag3)
        f_ag3 += A * (B * d * (n - 2) - 3 * f_ag2)
        f_ag2 += d * B

    # Compute variance
    f_var = f_ag2 / n

    # Compute skewness and kurtosis depending on variance
    if f_var > 0.:
        nvar = n * f_var
        f_g1, f_g2 = f_ag3 / (nvar * math.sqrt(f_var)), f_ag4 / (nvar * f_var)
    else:
        f_g1, f_g2 = math.nan, math.nan

    # Return descriptive statistics instance
    return Statistics(n, f_min, f_ave, f_max, f_var, f_g1, f_g2)


def print_function_statistics(values, function, var_name, logger: Logger):
    """Compute and report descriptive statistics of function values."""

    # Compute statistics
    logger.info(f"Descriptive statistics of {var_name}:")
    stats = compute_function_statistics(values, function)

    # Print detailed load information if requested
    for i, v in enumerate(values):
        logger.debug(f"\t{i}: {function(v)}")

    # Print summary
    for key_tuples in [
        ("cardinality", "sum", "imbalance"),
        ("minimum", "average", "maximum"),
        ("standard deviation", "variance"),
        ("skewness", "kurtosis")]:
        logger.info('\t' + ' '.join([
            f"{k}: {stats.statistics[k]:.6g}" for k in key_tuples]))

    # Return descriptive statistics instance
    return stats


def print_subset_statistics(subset_name, subset_size, set_name, set_size, logger: Logger):
    """Compute and report descriptive statistics of subset vs. full set."""

    # Print summary
    ss = f"{100. * subset_size / set_size:.3g}" if set_size else ''
    logger.info(f"{subset_name}: {subset_size:.6g} amongst {set_size:.6g} {set_name} ({ss}%)")

def compute_all_reachable_arrangements(objects: tuple, arrangement: tuple, alpha: float, beta: float, gamma: float,
                                       w_max: float, n_ranks: int, logger: Logger, max_objects: int = None):
    """Compute all arrangements reachable by moving up to a maximum number of objects."""

    logger.warning("Old function. Used by the removed Rank Object Enumerator script")

    # Storage for all reachable arrangements with their maximum work
    reachable = {}

    # Loop over all possible senders
    for from_id in range(n_ranks):
        # Loop over all possible receivers
        for to_id in range(n_ranks):
            if from_id == to_id:
                continue
            reachable.update(compute_pairwise_reachable_arrangements(objects, arrangement, alpha, beta, gamma, w_max,
                                                                     from_id, to_id, n_ranks, max_objects, logger))
    logger.info(
        f"Found {len(reachable)} reachable arrangements, with maximum work: {max(reachable.values())}:")
    for k, v in reachable.items():
        logger.info(f"\t{k}: {v}")

    # Return dict of reachable arrangements
    return reachable


def recursively_compute_transitions(stack: list, visited: dict, objects: tuple, arrangement: tuple, alpha: float,
                                    beta: float, gamma: float, w_max: float, w_min_max: float, n_ranks: int,
                                    logger: Logger, max_objects: Optional[int] = None):
    """Recursively compute all possible transitions to reachable arrangements from initial one."""

    logger.warning("Old function. Used by the removed Rank Object Enumerator script")

    # Sanity checks regarding current arrangement
    w_a = visited.get(arrangement, -1.)
    if w_a < 0.:
        logger.error(f"Arrangement {arrangement} not found in visited map")
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