#
#@HEADER
###############################################################################
#
#                                  lbsPhase.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
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
########################################################################
from logging import Logger
import random as rnd
import sys
import time

from src.Model.lbsObject import Object
from src.Model.lbsRank import Rank
from src.Model.lbsObjectCommunicator import ObjectCommunicator

from src.IO.lbsStatistics import print_subset_statistics, print_function_statistics, sampler
from src.IO.lbsVTStatisticsReader import LoadReader


class Phase:
    """A class representing the state of collection of ranks with
    objects at a given round
    """

    def __init__(self, t=0, logger: Logger = None, logging_level: str = 'info', file_suffix="vom"):
        # Initialize empty list of ranks
        self.ranks = []

        # Default time-step/phase of this phase
        self.phase_id = t

        # Initialize gossiping round
        self.round_index = 0

        # Assign logger to instance variable
        self.lgr = logger

        # Pass info when in debug mode
        self.logging_level = logging_level

        # Start with empty edges cache
        self.edges = {}
        self.cached_edges = False

        # Data files suffix(reading from data)
        self.file_suffix = file_suffix

    def get_ranks(self):
        """Retrieve ranks belonging to phase
        """
        return self.ranks

    def get_ranks_ids(self):
        """Retrieve IDs of ranks belonging to phase
        """
        return [p.get_id() for p in self.ranks]

    def get_phase_id(self):
        """Retrieve the time-step/phase for this phase
        """
        return self.phase_id

    def compute_edges(self):
        """Compute and return map of communication link IDs to volumes
        """
        # Compute or re-compute edges from scratch
        self.lgr.debug("Computing inter-process communication edges")
        self.edges.clear()
        directed_edges = {}

        # Initialize count of loaded ranks
        n_loaded = 0

        # Initialize sum of total and rank-local volumes
        v_total, v_local = 0., 0.

        # Iterate over ranks
        for p in self.ranks:
            # Retrieve sender rank ID
            i = p.get_id()
            self.lgr.debug(f"\trank {i}:")

            # Iterate over objects of current rank
            for o in p.get_objects():
                self.lgr.debug(f"\t* object {o.get_id()}:")

                # Iterate over recipient objects
                for q, volume in o.get_sent().items():
                    # Update total volume
                    v_total += volume

                    # Retrieve recipient rank ID
                    j = q.get_rank_id()
                    self.lgr.debug(f"\tsent volume {volume} to object {q.get_id()} assigned to rank {j}")

                    # Skip rank-local communications
                    if i == j:
                        # Update sum of local volumes and continue
                        v_local += volume
                        continue

                    # Create or update an inter-rank directed edge
                    ij = frozenset([i, j])
                    directed_edges.setdefault(ij, [0., 0.])
                    if i < j :
                        directed_edges[ij][0] += volume
                    else:
                        directed_edges[ij][1] += volume
                    self.lgr.debug(f"\tedge rank {i} --> rank {j}, volume: {directed_edges[ij]}")

        # Reduce directed edges into undirected ones with maximum
        for k, v in directed_edges.items():
            self.edges[k] = max(v)

        # Edges cache was fully updated
        self.cached_edges = True

        # Report on computed edges
        n_ranks = len(self.ranks)
        n_edges = len(self.edges)
        print_subset_statistics(
            "Inter-rank communication edges",
            n_edges,
            "possible ones", n_ranks * (n_ranks - 1) / 2,
            logger=self.lgr)
        print_subset_statistics(
            "Rank-local communication volume",
            v_local,
            "total volume",
            v_total,
            logger=self.lgr)

    def get_edges(self):
        """Retrieve edges belonging to phase
        """

        # Force recompute if edges cache is not current
        if not self.cached_edges:
            self.compute_edges()

        # Return cached edges
        return self.edges

    def invalidate_edge_cache(self):
        """Mark cached edges as no longer current
        """

        self.cached_edges = False

    def populate_from_samplers(self, n_o, ts, ts_params, c_degree, cs, cs_params, n_p, s_s=0):
        """Use samplers to populate either all or n procs in an phase
        """

        # Retrieve desired time sampler with its theoretical average
        time_sampler, sampler_name = sampler(ts, ts_params, logger=self.lgr)

        # Create n_o objects with uniformly distributed times in given range
        self.lgr.info(f"Creating {n_o} objects with times sampled from {sampler_name}")
        objects = set([Object(i, time_sampler()) for i in range(n_o)])

        # Compute and report object time statistics
        print_function_statistics(
            objects,
            lambda x: x.get_time(),
            "object times",
            logger=self.lgr)

        # Decide whether communications must be created
        if c_degree > 0:
            # Instantiante communication samplers with requested properties
            volume_sampler, volume_sampler_name = sampler(cs, cs_params, logger=self.lgr)

            # Create symmetric binomial sampler capped by number of objects for degree
            p_b = .5
            degree_sampler, degree_sampler_name = sampler(
                "binomial", [min(n_o - 1, int(c_degree / p_b)), p_b],
                logger=self.lgr)
            self.lgr.info(
                f"Creating communications with: \n\tvolumes sampled from {volume_sampler_name}\n\tout-degrees sampled from {degree_sampler_name}")

            # Create communicator for each object with only sent communications
            start = time.time()
            for obj in objects:
                # Create object communicator with outgoing messages
                obj.set_communicator(ObjectCommunicator(
                    {},
                    {o: volume_sampler() for o in rnd.sample(objects.difference([obj]), degree_sampler())},
                    obj.get_id(),
                    logger=self.lgr
                ))
            self.lgr.info(f"\tgenerated in {time.time() - start:.6g} seconds")

            # Create symmetric received communications
            for obj in objects:
                for k, v in obj.get_communicator().get_sent().items():
                    k.get_communicator().get_received()[obj] = v

        # Iterate over all object communicators to valid global communication graph
        v_sent, v_recv = [], []
        for obj in objects:
            i = obj.get_id()
            self.lgr.debug(f"\tobject {i}:")

            # Retrieve communicator and proceed to next object if empty
            comm = obj.get_communicator()
            if not comm:
                self.lgr.debug("\t  None")
                continue

            # Check and summarize communications and update global counters
            v_out, v_in = comm.summarize(
                '\t' if self.logging_level == "debug" else None)
            v_sent += v_out
            v_recv += v_in

        # Perform sanity checks
        if len(v_recv) != len(v_sent):
            self.lgr.error(f"Number of sent and received communications differ: {len(v_sent)} <> {len(v_recv)}")
            sys.exit(1)

        # Compute and report communication volume statistics
        print_function_statistics(
            v_sent,
            lambda x: x,
            "communication volumes",
            logger=self.lgr)

        # Create n_p ranks
        self.ranks = [Rank(i, logger=self.lgr) for i in range(n_p)]

        # Randomly assign objects to ranks
        if s_s and s_s <= n_p:
            self.lgr.info(f"Randomly assigning objects to {s_s} ranks amongst {n_p}")
        else:
            # Sanity check
            if s_s > n_p:
                self.lgr.warning(
                    f"Too many ranks ({s_s}) requested: only {n_p} available.")
                s_s = n_p
            self.lgr.info(f"Randomly assigning objects to {n_p} ranks")
        if s_s > 0:
            # Randomly assign objects to a subset o ranks of size s_s
            proc_list = rnd.sample(self.ranks, s_s)
            for o in objects:
                p = rnd.choice(proc_list)
                p.add_object(o)
                o.set_rank_id(p.get_id())
        else:
            # Randomly assign objects to all ranks
            for o in objects:
                p = rnd.choice(self.ranks)
                p.add_object(o)
                o.set_rank_id(p.get_id())

        # Print debug information when requested
        for p in self.ranks:
            self.lgr.debug(f"\t{p.get_id()} <- {p.get_object_ids()}")

    def populate_from_log(self, n_p, t_s, basename):
        """Populate this phase by reading in a load profile from log files
        """

        # Instantiate VT load reader
        reader = LoadReader(basename, logger=self.lgr, file_suffix=self.file_suffix)

        # Populate phase with reader output
        self.lgr.info(f"Reading objects from time-step {t_s} of VOM files with prefix {basename}")
        self.ranks = reader.read_iteration(n_p, t_s)

        # Compute and report object statistics
        objects = set()
        for p in self.ranks:
            objects = objects.union(p.get_objects())
        print_function_statistics(
            objects,
            lambda x: x.get_time(),
            "object times",
            logger=self.lgr)

        # Return number of found objects
        return len(objects)
