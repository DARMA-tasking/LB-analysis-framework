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
from logging import Logger
import os
import sys
import math
import itertools
import yaml
import csv

from src.IO.lbsLoadReaderVT import LoadReader
from src.Utils.logger import logger

project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])


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
ALPHA = CONF.get("work_model").get("parameters").get("alpha")
BETA = CONF.get("work_model").get("parameters").get("beta")
GAMMA = CONF.get("work_model").get("parameters").get("gamma")
INPUT_DATA = os.path.join(project_path, CONF.get("log_file"))
FILE_SUFFIX = CONF.get("file_suffix")
LGR = logger()


def get_objects(n_ranks: int, logger: Logger, file_prefix: str, file_suffix: str) -> tuple:
    """ Reads data from configuration and returns a tuple of objects with communication. """
    # Instantiate data containers
    objcts = list()
    communication = dict()

    # Instantiate data reader Class
    lr = LoadReader(file_prefix=file_prefix, logger=logger, file_suffix=file_suffix)

    # Iterate over ranks, collecting objects and communication
    for rank in range(n_ranks):
        iter_map, comm = lr.read(node_id=rank)
        for rnk in iter_map.values():
            for obj in rnk.migratable_objects:
                objcts.append({"id": obj.index, "time": obj.time})
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
    objcts.sort(key=lambda x: x.get("id"))

    # Adding communication to objects
    for objct in objcts:
        idx = objct.get("id")
        if communication.get(idx) is not None:
            objct.update(communication.get(idx))

    return tuple(objcts)


def compute_load(objects: tuple, object_list: list) -> float:
    """ Returns a load as a sum of all object times. """
    return sum([objects[i]["time"] for i in object_list])


def compute_volume(objects: tuple, rank_objects: list, direction: str) -> float:
    """ Returns a volume of rank objects. """
    # Initialize volume
    volume = 0.

    # Iterate over all rank objects
    for o in rank_objects:
        volume += sum([v for k, v in objects[o].get(direction, 0.).items() if k not in rank_objects])

    # Return computed volume
    return volume


def compute_arrangement_works(objects: tuple, arrngmnt: tuple, alpha_c: float, beta_c: float, gamma_c: float) -> dict:
    """ Returns a dictionary with works of rank objects. """
    # Build object rank map from arrangement
    ranks = {}
    for i, j in enumerate(arrngmnt):
        ranks.setdefault(j, []).append(i)

    # iterate over ranks
    works = {}
    for rank, rank_objects in ranks.items():
        # Compute per-rank loads
        works[rank] = alpha_c * compute_load(objects, rank_objects)

        # Compute communication volumes
        works[rank] += beta_c * max(compute_volume(objects, rank_objects, "from"),
                                    compute_volume(objects, rank_objects, "to"))

        # Add constant
        works[rank] += gamma_c

    # Return arrangement works
    return works


if __name__ == '__main__':
    # Getting objects from log files
    objcts = get_objects(n_ranks=N_RANKS, logger=LGR, file_prefix=INPUT_DATA, file_suffix=FILE_SUFFIX)

    # Print out input parameters
    LGR.info(f"alpha: {ALPHA}")
    LGR.info(f"beta: {BETA}")
    LGR.info(f"gamma: {GAMMA}")

    # Report on some initial configuration
    initial_arrangement = (0, 0, 0, 0, 1, 1, 1, 1, 2)
    LGR.info(f"Initial arrangement: {initial_arrangement}")
    initial_works = compute_arrangement_works(objcts, initial_arrangement, ALPHA, BETA, GAMMA)
    LGR.info(f"\tper-rank works: {initial_works}")
    LGR.info(f"\tmaximum work: {max(initial_works.values()):.4g} average work: "
             f"{(sum(initial_works.values()) / len(initial_works)):.4g}")

    # Generate all possible arrangements with repetition
    n_arrangements = 0
    works_min_max = math.inf
    arrangements_min_max = []
    for arrangement in itertools.product(range(N_RANKS), repeat=len(objcts)):
        # Compute per-rank works for currrent arrangement
        works = compute_arrangement_works(objcts, arrangement, ALPHA, BETA, GAMMA)

        # Update minmax when relevant
        work_max = max(works.values())
        if work_max < works_min_max:
            works_min_max = work_max
            arrangements_min_max = [arrangement]
        elif work_max == works_min_max:
            arrangements_min_max.append(arrangement)

        # Keep track of number of arrangements for sanity
        n_arrangements += 1

    # Sanity check
    LGR.info(f"Number of generated arrangements: {n_arrangements}")
    if n_arrangements != N_RANKS ** len(objcts):
        LGR.error("Incorrect number of arrangements")
        sys.exit(1)

    # Report on optimal arrangements
    LGR.info(f"\tminimax work: {works_min_max:.4g} for {len(arrangements_min_max)} arrangements")

    # Write all optimal arrangements to CSV file
    output_dir = os.path.join(project_path, CONF.get("output_dir"))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    out_name = os.path.join(output_dir, "optimal-arrangements.csv")
    with open(out_name, 'w') as f:
        writer = csv.writer(f)
        for a in arrangements_min_max:
            writer.writerow(a)
    LGR.info(f"Wrote {len(arrangements_min_max)} optimal arrangement to {out_name}")
