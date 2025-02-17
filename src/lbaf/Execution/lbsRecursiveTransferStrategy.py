#
#@HEADER
###############################################################################
#
#                       lbsRecursiveTransferStrategy.py
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
import math
import random
from bisect import bisect
from itertools import accumulate
from logging import Logger
from typing import Union

from .lbsTransferStrategyBase import TransferStrategyBase
from ..Model.lbsPhase import Phase


class RecursiveTransferStrategy(TransferStrategyBase):
    """A concrete class for the recursive transfer strategy."""

    def __init__(self, criterion, parameters: dict, logger: Logger):
        """Class constructor.

        :param criterion: a CriterionBase instance
        :param parameters: a dictionary of parameters.
        """
        # Call superclass init
        super().__init__(criterion, parameters, logger)

        # Select object order strategy
        self.__strategy_mapped = {
            "arbitrary": self.arbitrary,
            "element_id": self.element_id,
            "decreasing_loads": self.decreasing_loads,
            "increasing_loads": self.increasing_loads,
            "fewest_migrations": self.fewest_migrations,
            "small_objects": self.small_objects}
        o_s = parameters.get("order_strategy")
        if o_s not in self.__strategy_mapped:
            self._logger.error(f"{o_s} does not exist in known ordering strategies: "
                                f"{list(self.__strategy_mapped)}")
            raise SystemExit(1)
        self.__order_strategy = self.__strategy_mapped[o_s]
        self._logger.info(f"Selected {self.__order_strategy.__name__} object ordering strategy")

    def __recursive_extended_search(self, pick_list, objects, c_fct, n_o, max_n_o):
        """Recursively extend search to other objects."""
        # Fail when no more objects available or maximum depth is reached
        if not pick_list or n_o >= max_n_o:
            return False

        # Pick one object and move it from one list to the other
        o = random.choice(pick_list)
        pick_list.remove(o)
        objects.append(o)
        n_o += 1

        # Decide whether criterion allows for transfer
        if c_fct(objects) < 0.0:
            # Transfer is not possible, recurse further
            return self.__recursive_extended_search(
                pick_list, objects, c_fct, n_o, max_n_o)

        # Succeed when criterion is satisfied
        return True

    def execute(self, known_peers, phase: Phase, ave_load: float, _):
        """Perform object transfer stage."""
        # Initialize transfer stage
        self._initialize_transfer_stage(ave_load)
        max_obj_transfers = 0

        # Map rank to targets and ordered migratable objects
        phase_ranks = phase.get_ranks()
        if self._deterministic_transfer:
            phase_ranks = sorted(phase_ranks, key=lambda r: r.get_id())
        rank_targets = self._get_ranks_to_traverse(phase_ranks, known_peers)

        # Iterate over traversable ranks
        for r_src, targets in rank_targets.items():
            # Try to recursively offload objects from source
            self._logger.debug(
                f"Trying to offload rank {r_src.get_id()} onto {[r.get_id() for r in targets]}:")
            srt_rank_obj = list(self.__order_strategy(
                r_src.get_migratable_objects(), r_src.get_id()))
            while srt_rank_obj:
                # Pick next object in ordered list
                o_src = [srt_rank_obj.pop()]
                self._logger.debug(f"\tobject {o_src[0].get_id()}:")

                # Initialize destination information
                r_dst, c_dst = None, -math.inf

                # Use deterministic or probabilistic transfer method
                if self._deterministic_transfer:
                    # Select best destination with respect to criterion
                    for r_try in targets:
                        c_try = self._criterion.compute(
                            r_src, o_src, r_try)
                        if c_try > c_dst:
                            c_dst, r_dst = c_try, r_try
                else:
                    # Pseudo-randomly select transfer destination
                    r_dst, c_dst = self._randomly_select_target(
                        r_src, o_src, targets)
                    if not r_dst:
                        self._n_rejects += 1
                        continue

                # Handle case where object not suitable for transfer
                if c_dst < 0.0:
                    # Give up if no objects left of no rank is feasible
                    if not srt_rank_obj or not r_dst:
                        self._n_rejects += 1
                        continue

                    # Recursively extend search if possible
                    pick_list = srt_rank_obj[:]
                    if self.__recursive_extended_search(
                        pick_list,
                        o_src,
                        lambda x, r_src=r_src, r_dst=r_dst: self._criterion.compute(r_src, x, r_dst),
                        1,
                        self._max_objects_per_transfer):
                        # Remove accepted objects from remaining object list
                        srt_rank_obj = pick_list
                    else:
                        # No transferable list of objects was found
                        self._n_rejects += 1
                        continue

                # Transfer objects
                if (n_o_src := len(o_src)) > max_obj_transfers:
                    max_obj_transfers = n_o_src
                self._logger.debug(f"Transferring {n_o_src} object(s)")
                self._n_transfers += phase.transfer_objects(r_src, o_src, r_dst)

        # Return transfer phase counts
        self._logger.info(
            f"Maximum number of objects transferred at once: {max_obj_transfers}")
        return len(phase_ranks) - len(rank_targets), self._n_transfers, self._n_rejects

    @staticmethod
    def arbitrary(objects: set, _):
        """Default: objects are passed as they are stored."""
        return objects

    @staticmethod
    def element_id(objects: set, _):
        """Order objects by ID."""
        return sorted(objects, key=lambda x: x.get_id())

    @staticmethod
    def decreasing_loads(objects: set, _):
        """Order objects by decreasing object loads."""
        return sorted(objects, key=lambda x: -x.get_load())

    @staticmethod
    def increasing_loads(objects: set, _):
        """Order objects by increasing object loads."""
        return sorted(objects, key=lambda x: x.get_load())

    @staticmethod
    def sorted_ascending(objects: Union[set, list]):
        """Order objects by ascending object loads."""
        return sorted(objects, key=lambda x: x.get_load())

    @staticmethod
    def sorted_descending(objects: Union[set, list]):
        """Order objects by descending object loads."""
        return sorted(objects, key=lambda x: -x.get_load())

    def load_excess(self, objects: set):
        """Determine the amount of excess load in the set of objects."""
        rank_load = sum(obj.get_load() for obj in objects)
        return rank_load - self._average_load

    def fewest_migrations(self, objects: set, _):
        """First find the load of the smallest single object that, if migrated
        away, could bring this rank's load below the target load.

        Sort largest to the smallest if <= load_excess
        Sort smallest to the largest if > load_excess.
        """
        load_excess = self.load_excess(objects)
        lt_load_excess = [obj for obj in objects if obj.get_load() <= load_excess]
        get_load_excess = [obj for obj in objects if obj.get_load() > load_excess]
        return self.sorted_descending(lt_load_excess) + self.sorted_ascending(get_load_excess)

    def small_objects(self, objects: set, _):
        """First find the smallest object that, if migrated away along with all
        smaller objects, could bring this rank's load below the target load.

        Sort largest to the smallest if <= load_excess
        Sort smallest to the largest if > load_excess.
        """

        load_excess = self.load_excess(objects)
        sorted_objects = self.sorted_ascending(objects)
        accumulated_loads = list(accumulate(obj.get_load() for obj in sorted_objects))
        idx = bisect(accumulated_loads, load_excess) + 1
        return self.sorted_descending(sorted_objects[:idx]) + self.sorted_ascending(sorted_objects[idx:])
