#
#@HEADER
###############################################################################
#
#                                lbsRuntime.py
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

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Execution.lbsAlgorithmBase import AlgorithmBase
from ..IO.lbsStatistics import compute_function_statistics, min_Hamming_distance


class Runtime:
    """A class to handle the execution of the LBS."""

    def __init__(
            self,
            phases: dict,
            work_model: dict,
            algorithm: dict,
            logger: Logger):
        """Class constructor.

        :param phases: dictionary of Phase instances
        :param work_model: dictionary with work model name and optional parameters
        :param algorithm: dictionary with algorithm name and parameters
        :param logger: logger for output messages
        """
        # Assign logger to instance variable
        self.__logger = logger

        # If no LBS phase was provided, do not do anything
        if not phases or not isinstance(phases, dict):
            self.__logger.error(
                "Could not create a runtime without a dictionary of phases")
            raise SystemExit(1)
        self.__phases = phases

        # Instantiate work model
        self.__work_model = WorkModelBase.factory(
            work_model.get("name"),
            work_model.get("parameters", {}),
            self.__logger)

        # Instantiate balancing algorithm
        self.__algorithm = AlgorithmBase.factory(
            algorithm.get("name"),
            algorithm.get("parameters", {}),
            self.__work_model,
            self.__logger)
        if not self.__algorithm:
            self.__logger.error(
                f"Could not instantiate an algorithm of type {self.__algorithm}")
            raise SystemExit(1)

        # Initialize run statistics
        phase_0 = self.__phases[min(self.__phases.keys())]
        l_stats = compute_function_statistics(
            phase_0.get_ranks(),
            lambda x: x.get_load())
        self.__statistics = {"average load": l_stats.get_average()}

    def get_work_model(self):
        """Return runtime work model."""
        return self.__work_model

    def execute(self, p_id: int, phase_increment: int=0, lb_iterations=False):
        """Execute runtime for single phase with given ID or multiple phases in selected range."""
        # Execute load balancing algorithm
        self.__logger.info(
            f"Executing {type(self.__algorithm).__name__} for "
            + ("all phases" if p_id < 0 else f"phase {p_id}"))
        self.__algorithm.execute(
            p_id,
            self.__phases,
            self.__statistics)

        # Retrieve possibly null rebalanced phase and return it
        if (lbp := self.__algorithm.get_rebalanced_phase()):
            # Retain lb iterations with initial phase when it is replaced
            if not phase_increment:
                self.__algorithm.get_rebalanced_phase().set_lb_iterations(
                self.__algorithm.get_initial_phase().get_lb_iterations())

            # Increment rebalanced phase ID as requested
            lbp.set_id((lbp_id := lbp.get_id() + phase_increment))

            # Share communications from original phase with new phase
            initial_communications = self.__algorithm.get_initial_communications()
            lbp.set_communications(initial_communications[p_id])
            self.__logger.info(f"Created rebalanced phase {lbp_id}")

        # Return rebalanced phase
        return lbp
