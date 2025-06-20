#
#@HEADER
###############################################################################
#
#                         lbsPhaseStepperAlgorithm.py
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
from logging import Logger
from .lbsAlgorithmBase import AlgorithmBase
from ..Model.lbsPhase import Phase
from ..IO.lbsStatistics import print_function_statistics

class PhaseStepperAlgorithm(AlgorithmBase):
    """A concrete class for the phase stepper non-optimzing algorithm."""

    def __init__(self, work_model, parameters: dict, lgr: Logger):
        """Class constructor

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        :param lgr: logger
        """
        # Call superclass init
        super().__init__(work_model, parameters, lgr)

    def execute(self, _, phases: list, statistics: dict):
        """Steps through all phases."""

        # Ensure that a list with at least one phase was provided
        if not isinstance(phases, dict) or not all(
                isinstance(p, Phase) for p in phases.values()):
            self._logger.error("Algorithm execution requires a dictionary of phases")
            raise SystemExit(1)

        # Iterate over all phases
        for p_id, self._rebalanced_phase in phases.items():
            # Step through current phase
            self._logger.info(f"Stepping through phase {p_id}")

            # Compute and report phase rank work statistics
            print_function_statistics(
                self._rebalanced_phase.get_ranks(),
                self._work_model.compute,
                f"phase {p_id} rank works",
                self._logger)

            # Update run statistics
            self._update_statistics(statistics)

            # Report current mapping in debug mode
            self._report_final_mapping(self._logger)

        # Indicate that no phase was modified
        self._rebalanced_phase = None
