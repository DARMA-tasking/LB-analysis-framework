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
import sys
import math
import itertools

# Dictionary of objects
objects = (
    {"id": 0, "time": 1.0},
    {"id": 1, "time": 0.5},
    {"id": 2, "time": 0.5},
    {"id": 3, "time": 0.5},
    {"id": 4, "time": 0.5},
    {"id": 5, "time": 2.0},
    {"id": 6, "time": 1.0},
    {"id": 7, "time": 0.5},
    {"id": 8, "time": 1.5})

# Define number of ranks
n_ranks = 4

# Define work constants
alpha = 1.
beta = 0.
gamma = 0.

def compute_load(object_list):
    # Load is sum of all object times
    return sum([objects[i]["time"] for i in object_list])

def compute_arrangement_works(arrangement, alpha, beta, gamma):
    # Build object rank map from arrangement
    ranks = {}
    for i, j in enumerate(arrangement):
        ranks.setdefault(j, []).append(i)

    # Compute per-object loads
    works = {}
    for k, v in ranks.items():
        works[k] = alpha * compute_load(v)

    # Return computed works
    return works

if __name__ == '__main__':
    # Report on some initial configuration
    initial_works = compute_arrangement_works(
        (0, 0, 0, 0, 1, 1, 1, 1, 2), alpha, beta, gamma)
    print("Initial works:", initial_works)
    print("\tmaximum work: {:.4g} average work: {:.4g}".format(
        max(initial_works.values()),
        sum(initial_works.values()) / len(initial_works)))
    
    # Generate all possible arrangements with repetition
    n_arrangements = 0
    works_min_max = math.inf
    arrangements_min_max = []
    for arrangement in itertools.product(range(n_ranks), repeat=len(objects)):
        # Compute per-rank works for currrent arrangement
        works = compute_arrangement_works(arrangement, alpha, beta, gamma)

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
    print("Number of generated arrangements:", n_arrangements)
    if n_arrangements != n_ranks ** len(objects):
        print("** ERROR: incorrect numnber of arrangements")
        sys.exit(1)

    # Report on optimal arrangements
    print("\tminimax work: {:.4g} for {} arrangements".format(
        works_min_max,
        len(arrangements_min_max)))
    print("Example optimal arrangement:", arrangements_min_max[0])
    optimal_works = compute_arrangement_works(
        arrangements_min_max[0], alpha, beta, gamma)
    print("\tmaximum work: {:.4g} average work: {:.4g}".format(
        max(optimal_works.values()),
        sum(optimal_works.values()) / len(optimal_works)))
