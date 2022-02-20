#@HEADER
###############################################################################
#
#                          rank-object-enumerator.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2021 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
###############################################################################
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
    exit(1)

from src.IO.lbsVTStatisticsReader import LoadReader
from src.Utils.logger import logger


def get_conf() -> dict:
    """ Gets config from file and returns a dictionary. """
    with open(os.path.join(project_path, "src", "Applications", "conf.yaml"), 'rt') as conf_file:
        conf = yaml.safe_load(conf_file)
    return conf

# Getting configuration:
CONF = get_conf()

# Define number of ranks
N_RANKS = CONF.get("x_procs") * CONF.get("y_procs") * CONF.get("z_procs")

# Define work constants
alpha_global = CONF.get("work_model").get("parameters").get("alpha")
beta_global = CONF.get("work_model").get("parameters").get("beta")
gamma_global = CONF.get("work_model").get("parameters").get("gamma")
INPUT_DATA = os.path.join(project_path, CONF.get("log_file"))
FILE_SUFFIX = CONF.get("file_suffix")
LGR = logger()


def get_objects(n_ranks: int, logger: Logger, file_prefix: str, file_suffix: str) -> tuple:
    """ Read data from configuration and returns a tuple of objects with communication
    """

    # Instantiate data containers
    objects = []
    communication = {}

    # Instantiate data reader Class
    lr = LoadReader(file_prefix=file_prefix, logger=logger, file_suffix=file_suffix)

    # Iterate over ranks, collecting objects and communication
    for rank in range(n_ranks):
        iter_map, comm = lr.read(node_id=rank)
        for rnk in iter_map.values():
            for obj in rnk.migratable_objects:
                objects.append({"id": obj.get_id(), "time": obj.time})
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


def compute_load(objects, rank_object_ids) -> float:
    """ Return a load as a sum of all object times
    """

    return sum([objects[i]["time"] for i in rank_object_ids])


def compute_volume(objects, rank_object_ids, direction: str) -> float:
    """ Return a volume of rank objects
    """

    # Initialize volume
    volume = 0.

    # Iterate over all rank objects
    for i in rank_object_ids:
        volume += sum(
            [v for k, v in objects[i].get(direction, 0.).items()
             if k not in rank_object_ids])

    # Return computed volume
    return volume


def compute_arrangement_works(objects: tuple, arrngmnt: tuple, alpha: float, beta: float, gamma: float) -> dict:
    """ Return a dictionary with works of rank objects
    """

    # Build object rank map from arrangement
    ranks = {}
    for i, j in enumerate(arrngmnt):
        ranks.setdefault(j, []).append(i)

    # iterate over ranks
    works = {}
    for rank, rank_objects in ranks.items():
        # Compute per-rank loads
        works[rank] = alpha * compute_load(objects, rank_objects)

        # Compute communication volumes
        works[rank] += beta * max(
            compute_volume(objects, rank_objects, "from"),
            compute_volume(objects, rank_objects, "to"))

        # Add constant
        works[rank] += gamma

    # Return arrangement works
    return works

def compute_pairwise_reachable_arrangements(objects, arrangement, alpha: float, beta: float, gamma: float, w_max: float, from_id: int, to_id: int, n_ranks:int, max_objects:int=None):
    """Compute arragnements reachable by moving up to a maximum number of objects from one rank to another
    """

    # Sanity checks regarding rank IDs
    if from_id >= n_ranks:
        LGR.error(f"Incorrect sender ID: {from_id} >= {n_ranks}")
        sys.exit(1)
    if to_id >= n_ranks:
        LGR.error(f"Incorrect receiver ID: {to_id} >= {n_ranks}")
        sys.exit(1)

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
            # Change all correspdonding entries
            n_possible += 1
            new_arrangement = tuple(
                to_id if i in c else r for i, r in enumerate(arrangement))
            works = compute_arrangement_works(
                objects,
                new_arrangement,
                alpha, beta, gamma)

            # Check whether new arrangements is reachable
            w_max_new = max(works.values())
            if w_max_new <= w_max:
                reachable[new_arrangement] = w_max_new
    LGR.debug(f"Found {len(reachable)} reachable arrangement(s) from rank {from_id} to rank {to_id} amongst {n_possible} possible one(s)")

    # Return dict of reachable arrangements
    return reachable

def compute_all_reachable_arrangements(objects, arrangement, alpha: float, beta: float, gamma: float, w_max: float, n_ranks:int, max_objects:int=None):
    """Compute all arragnements reachable by moving up to a maximum number of objects
    """

    # Storage for all reachable arrangements with their maximum work
    reachable = {}

    # Loop over all possible senders
    for from_id in range(n_ranks):
        # Loop over all possible receivers
        for to_id in range(n_ranks):
            if from_id == to_id:
                continue
            reachable.update(compute_pairwise_reachable_arrangements(
                objects,
                initial_arrangement,
                alpha_global, beta_global, gamma_global,
                w_max,
                from_id, to_id, n_ranks,
                max_objects))
    LGR.info(f"Found {len(reachable)} reachable arrangements, with minimum maximum work: {min(reachable.values())}:")
    for k, v in reachable.items():
            LGR.info(f"\t{k}: {v}")

    # Return dict of reachable arrangements
    return reachable

def compute_min_max_arrangements_work(objects):
    """Compute all possible arrangements with repetition and minimax work
    """

    # Initialize quantities of interest
    n_arrangements = 0
    works_min_max = math.inf
    arrangements_min_max = []
    for arrangement in itertools.product(
        range(N_RANKS),
        repeat=len(objects)):

        # Compute per-rank works for currrent arrangement
        works = compute_arrangement_works(
            objects,
            arrangement,
            alpha_global, beta_global, gamma_global)

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
    
if __name__ == '__main__':

    # Get objects from log files
    objects = get_objects(
        n_ranks=N_RANKS,
        logger=LGR,
        file_prefix=INPUT_DATA,
        file_suffix=FILE_SUFFIX)

    # Print out input parameters
    LGR.info(f"alpha: {alpha_global}")
    LGR.info(f"beta: {beta_global}")
    LGR.info(f"gamma: {gamma_global}")

    # Compute and report on best possible arrangements
    n_a, w_min_max, a_min_max = compute_min_max_arrangements_work(objects)
    if n_a != N_RANKS ** len(objects):
        LGR.error("Incorrect number of possible arrangements with repetition")
        sys.exit(1)
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

    # Report on some initial configuration
    initial_arrangement =  (3, 0, 0, 0, 0, 1, 3, 3, 2)
    LGR.info(f"Initial arrangement: {initial_arrangement}")
    initial_works = compute_arrangement_works(
        objects,
        initial_arrangement,
        alpha_global, beta_global, gamma_global)
    w_max = max(initial_works.values())
    LGR.info(f"\tper-rank works: {initial_works}")
    LGR.info(f"\tmaximum work: {w_max:.4g} average work: "
             f"{(sum(initial_works.values()) / len(initial_works)):.4g}")

    # Compute all possible reachable arrangements
    all_reachable = compute_all_reachable_arrangements(
        objects,
        initial_arrangement,
        alpha_global, beta_global, gamma_global,
        w_max,
        N_RANKS)

    print(all_reachable)
