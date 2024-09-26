#
#@HEADER
###############################################################################
#
#                          lbsBruteForceAlgorithm.py
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
"""lbsBruteForceAlgorithm"""
from logging import Logger

from ..Model.lbsAffineCombinationWorkModel import AffineCombinationWorkModel
from .lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import compute_min_max_arrangements_work


class BruteForceAlgorithm(AlgorithmBase):
    """A concrete class for the brute force optimization algorithm"""

    def __init__(self, work_model, parameters: dict, lgr: Logger, rank_qoi: str, object_qoi: str):
        """Class constructor.

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        :param rank_qoi: rank QOI to track
        :param object_qoi: object QOI to track.
        """
        # Call superclass init
        super(BruteForceAlgorithm, self).__init__(
            work_model, parameters, lgr, rank_qoi, object_qoi)

        # Assign optional parameters
        self.__skip_transfer = parameters.get("skip_transfer", False)
        self._logger.info(
            f"Instantiated {'with' if self.__skip_transfer else 'without'} transfer stage skipping")

    def execute(self, p_id: int, phases: list, distributions: dict, statistics: dict, _):
        """Execute brute force optimization algorithm on phase with index p_id."""
        # Perform pre-execution checks and initializations
        self._initialize(p_id, phases, distributions, statistics)
        self._logger.info("Starting brute force optimization")
        initial_phase = phases[min(phases.keys())]
        phase_ranks = initial_phase.get_ranks()
        objects = initial_phase.get_objects()
        n_ranks = len(phase_ranks)
        affine_combination = isinstance(
            self._work_model, AffineCombinationWorkModel)
        alpha, beta, gamma = [
            self._work_model.get_alpha() if affine_combination else 1.0,
            self._work_model.get_beta() if affine_combination else 0.0,
            self._work_model.get_gamma() if affine_combination else 0.0]
        _n_a, _w_min_max, a_min_max = compute_min_max_arrangements_work(objects, alpha, beta, gamma, n_ranks,
                                                                        logger=self._logger)

        # Skip object transfers when requested
        if self.__skip_transfer:
            self._logger.info("Skipping object transfers")
            return

        # Pick first optimal arrangement and reassign objects accordingly
        n_transfers = 0
        arrangement = a_min_max[0]
        self._logger.debug(
            f"Reassigning objects with arrangement {arrangement}")
        for i, a in enumerate(arrangement):
            # Skip objects that do not need transfer
            r_src = phase_ranks[objects[i].get_rank_id()]
            r_dst = phase_ranks[a]
            if r_src == r_dst:
                continue

            # Otherwise locate object on source and transfer to destination
            object_id = objects[i].get_id()
            for o in r_src.get_objects():
                if o.get_id() == object_id:
                    # Perform transfer
                    self._rebalanced_phase.transfer_object(r_src, o, r_dst)
                    n_transfers += 1

        # Report on object transfers
        self._logger.info(f"{n_transfers} transfers occurred")

        # Update run distributions and statistics
        self._update_distributions_and_statistics(distributions, statistics)

        # Report final mapping in debug mode
        self._report_final_mapping(self._logger)
