#
#@HEADER
###############################################################################
#
#                  lbsCentralizedPrefixOptimizerAlgorithm.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
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
import heapq
from logging import Logger

from .lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import print_function_statistics


class CentralizedPrefixOptimizerAlgorithm(AlgorithmBase):
    """ A concrete class for the centralized prefix memory-constrained optimizer"""

    def __init__(self, work_model, parameters: dict, lgr: Logger):
        """ Class constructor
            work_model: a WorkModelBase instance
            parameters: a dictionary of parameters."""

        # Call superclass init
        super().__init__(work_model, parameters, lgr)

        self._do_second_stage = parameters.get("do_second_stage", False)
        self._phase = None
        self._max_shared_ids = None

    def execute(self, p_id: int, phases: list, statistics: dict, _):
        """ Execute centralized prefix memory-constrained optimizer"""

        p_id = 0

        # Ensure that a list with at least one phase was provided
        self._initialize(p_id, phases, statistics)

        self._phase = self._rebalanced_phase

        # Initialize run statistics
        self._update_statistics(statistics)

        # Prepare input data for rank order enumerator
        self._logger.info("Starting optimizer")
        phase_ranks = self._phase.get_ranks()

        # Initialize max shared ID
        max_shared_ids = 0
        for rank in phase_ranks:
            max_shared_ids = max(len(rank.get_shared_ids()), max_shared_ids)
        self._max_shared_ids = max_shared_ids + 1


        # Max-heap for rank's load
        rank_max_heap = []

        # Add the ranks to the list
        for rank in phase_ranks:
            rank_max_heap.append(rank)

        # Iterate until number of assignments reached
        made_no_assignments = 0
        while made_no_assignments < 2:
            # Make the actual heap
            heapq._heapify_max(rank_max_heap)

            # Get the max rank from the heap
            max_rank = heapq._heappop_max(rank_max_heap)

            # Amount of load we should remove from the max rank to bring it to average
            diff = max_rank.get_load() - statistics["average load"]
            self._logger.info(f"diff={diff}")

            # Keep track of objects that share memory and the load sums for them
            shared_map, obj_shared_map = {}, {}

            # Array of loads grouped by shared ID, and prefix array after sorted
            groupings, groupings_sum = [], []

            # Fill up the data structures
            for o in max_rank.get_migratable_objects():
                if not o.get_shared_id() in obj_shared_map:
                    obj_shared_map[o.get_shared_id()] = []
                if not o.get_shared_id() in shared_map:
                    shared_map[o.get_shared_id()] = 0
                obj_shared_map[o.get_shared_id()].append(o)
                shared_map[o.get_shared_id()] += o.get_load()

            for sid, value in obj_shared_map.items():
                value.sort(reverse=True, key=lambda x: x.get_load())

            for sid, value in shared_map.items():
                groupings.append((value, sid))

            # Sort the groupings so we can compute the prefix sum
            groupings.sort()

            # Compute the prefix sum of grouped loads by shared ID
            for i in range(len(groupings)):
                groupings_sum.append(0)
            groupings_sum[0] = groupings[0][0]
            for i in range(1,len(groupings)):
                groupings_sum[i] = groupings_sum[i-1] + groupings[i][0]

            for i in range(len(groupings)):
                self._logger.info(f"i={i} sum={groupings_sum[i]}")

            # Pick a bracketed range of grouped loads to consider for migration
            # The range should be sufficiently large enough to get us down to
            # the average
            pick_upper = 0
            while groupings_sum[pick_upper] < diff:
                pick_upper += 1
            if pick_upper-1 >= 0 and groupings_sum[pick_upper-1] >= diff * 1.05:
                pick_upper -= 1
            pick_lower = pick_upper-1
            while (pick_lower-1 >= -1 and groupings_sum[pick_upper] - groupings_sum[pick_lower] < diff):
                pick_lower -= 1

            self._logger.info(f"pick=({pick_lower},{pick_upper}]")

            made_assignment = False

            if made_no_assignments and self._do_second_stage:
                for i, (size, sid) in enumerate(groupings):
                    ret = self._consider_swaps(phase_ranks, max_rank, i, size, sid, diff, obj_shared_map)
                    made_assignment = made_assignment or ret
                    if ret:
                        break
                # for i in reversed(range(0,len(groupings))):
                #     size = groupings[i][0]
                #     sid = groupings[i][1]
                #     ret = self._try_bin_fully(phase_ranks, max_rank, i, size, sid, obj_shared_map)
                #     made_assignment = made_assignment or ret
                #     if made_assignment:
                #         made_no_assignments = 0
                #     if ret:
                #         break;
            else:
                for i in range(pick_lower+1,pick_upper+1):
                    size = groupings[i][0]
                    sid = groupings[i][1]
                    ret = self._try_bin(phase_ranks, max_rank, i, size, sid, obj_shared_map)
                    made_assignment = made_assignment or ret

            # Add max rank back to the heap
            rank_max_heap.append(max_rank)

            if not made_assignment:
                made_no_assignments += 1
            else:
                # Compute and report iteration work statistics
                print_function_statistics(
                    self._phase.get_ranks(),
                    self._work_model.compute,
                    f"iteration {i + 1} rank work",
                    self._logger)

                # Update run statistics
                self._update_statistics(statistics)

        # Report final mapping in debug mode
        self._report_final_mapping(self._logger)

    def _try_bin(self, ranks, max_rank, tbin, size, sid, objs):
        """Try to find a rank to offload a bin (load grouping that shares a common memory ID)"""

        # Min-heap of ranks
        rank_min_heap = []

        # Add all ranks that could possibly take this load grouping based on memory usage
        self._logger.info(f"tryBin size={size}, max={self._max_shared_ids}")
        for rank in ranks:
            if sid in rank.get_shared_ids() or len(rank.get_shared_ids()) < self._max_shared_ids:
                rank_min_heap.append(rank)

        # Create the actual min-heap
        heapq.heapify(rank_min_heap)

        # The selected rank
        min_rank = None

        tally_assigned, tally_rejected = 0, 0

        for o in objs[sid]:
            if len(rank_min_heap) == 0:
                self._logger.error("Reached condition where no ranks could take the element!")
                raise SystemExit(1)

            # Pick the rank that is most underloaded (greedy)
            if min_rank is None:
                min_rank = heapq.heappop(rank_min_heap)

            selected_load = o.get_load()

            # If our situation is not made worse and fits under memory constraints, do the transer
            if (sid in min_rank.get_shared_ids() or \
                len(min_rank.get_shared_ids()) < self._max_shared_ids) and \
                min_rank.get_load() + selected_load < max_rank.get_load():
                self._phase.transfer_object(max_rank, o, min_rank)
                tally_assigned += 1
            else:
                # Put the rank back in the heap for selection next round
                if not(len(min_rank.get_shared_ids()) >= self._max_shared_ids and \
                   not sid in min_rank.get_shared_ids()):
                    heapq.heappush(rank_min_heap, min_rank)

                tally_rejected += 1

        self._logger.info(
            f"tryBin: {tbin}, size={size}, id={sid}; assigned={tally_assigned}, rejected={tally_rejected}")

        return tally_assigned > 0

    def _try_bin_fully(self, ranks, max_rank, tbin, size, sid, objs):
        """Try to find a rank to offload a bin (load grouping that shares a
        common memory ID), but do not give up unless there is absolutely no
        rank that can take it"""

        self._logger.info(f"tryBinFully size={size}, max={self._max_shared_ids}")

        tally_assigned, tally_rejected = 0, 0

        for o in objs[sid]:
            # Min-heap of ranks
            rank_min_heap = []

            # Add all ranks that could possibly take this load grouping based on
            # memory usage
            for rank in ranks:
                if sid in rank.get_shared_ids() or len(rank.get_shared_ids()) < self._max_shared_ids:
                    rank_min_heap.append(rank)

            # Create the actual min-heap
            heapq.heapify(rank_min_heap)

            while len(rank_min_heap) > 0:
                # Pick the rank that is most underloaded (greedy)
                min_rank = heapq.heappop(rank_min_heap)

                selected_load = o.get_load()

                # If our situation is not made worse and fits under memory constraints, do the transer
                if (sid in min_rank.get_shared_ids() or \
                    len(min_rank.get_shared_ids()) < self._max_shared_ids) and \
                    min_rank.get_load() + selected_load < max_rank.get_load():
                    self._phase.transfer_object(max_rank, o, min_rank)
                    tally_assigned += 1
                    break

                tally_rejected += 1

        self._logger.info(
            f"tryBinFully: {tbin}, size={size}, id={sid}; assigned={tally_assigned}, rejected={tally_rejected}")

        return tally_assigned > 0

    def _consider_swaps(self, ranks, max_rank, tbin, size, sid, diff, objs):
        if size > diff * 0.3:
            self._logger.info(f"considerSwaps: bin={tbin}, size={size}, diff={diff}")
        else:
            return False

        rank_min_heap = []

        # Add all ranks that could possibly take this load grouping
        for rank in ranks:
            rank_min_heap.append(rank)

        # Create the actual min-heap
        heapq.heapify(rank_min_heap)

        while len(rank_min_heap) > 0:
            # Pick the rank that is most underloaded (greedy)
            min_rank = heapq.heappop(rank_min_heap)

            if min_rank == max_rank:
                continue

            binned = {}

            for o in min_rank.get_migratable_objects():
                if not o.get_shared_id() in binned:
                    binned[o.get_shared_id()] = []
                binned[o.get_shared_id()].append(o)

            pick = -1

            for y, objects in binned.items():
                load_sum = 0.0
                for x in objects:
                    load_sum += x.get_load()

                cur_max = max_rank.get_load()

                if min_rank.get_load() + size - load_sum < cur_max and max_rank.get_load() - size + load_sum < cur_max:
                    self._logger.info(
                        f"considerSwaps: continue testing: {cur_max}, "
                        f"new min={min_rank.get_load() + size - load_sum}, "
                        f"new max={max_rank.get_load() - size + load_sum}"
                    )
                else:
                    self._logger.info(
                        f"considerSwaps: would make situation worse: {cur_max}, "
                        f"new min={min_rank.get_load() + size - load_sum}, "
                        f"new max={max_rank.get_load() - size + load_sum}"
                    )
                    continue

                if load_sum*1.1 < diff:
                    pick = y
                    break

            if pick != -1:
                for o in binned[pick]:
                    self._phase.transfer_object(min_rank, o, max_rank)
                for o in objs[sid]:
                    self._phase.transfer_object(max_rank, o, min_rank)
                return True

        return False
