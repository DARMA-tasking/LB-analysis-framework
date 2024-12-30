#
#@HEADER
###############################################################################
#
#                             lbsAlgorithmBase.py
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
import abc
from typing import List

from ..IO.lbsStatistics import compute_function_statistics
from ..Model.lbsNode import Node
from ..Model.lbsPhase import Phase
from ..Model.lbsWorkModelBase import WorkModelBase
from ..Utils.lbsLogging import Logger

class AlgorithmBase:
    """An abstract base class of load/work balancing algorithms."""
    __metaclass__ = abc.ABCMeta

    # Protected logger
    _logger: Logger

    # Concrete algorithms need a work model
    _work_model: WorkModelBase=None

    # Iterative algorithms are allowed to store load balancing iterations
    _lb_iterations: List[Phase]

    def __init__(self, work_model: WorkModelBase, parameters: dict, logger: Logger):
        """Class constructor.

        :param work_model: a WorkModelBase instance
        :param parameters: a dictionary of parameters
        """
        # Assert that a logger instance was passed
        if not isinstance(logger, Logger):
            self._logger.error(f"Incorrect type {type(logger)} passed instead of Logger instance")
            raise SystemExit(1)
        self._logger = logger

        # Assert that a work model base instance was passed
        if not isinstance(work_model, WorkModelBase):
            self._logger.error("Could not create an algorithm without a work model")
            raise SystemExit(1)
        self._work_model = work_model

        # Assert that a parameters dict was passed
        if not isinstance(parameters, dict):
            self._logger.error("Could not create an algorithm without a dictionary of parameters")
            raise SystemExit(1)

        # By default algorithms are not assumed to be iterative
        self._lb_iterations = []

        # Initially no phases are assigned for rebalancing
        self._initial_phase = None
        self._rebalanced_phase = None

        # Keep track of phase communications
        self._initial_communications = {}

        # Map rank statistics to their respective computation methods
        self.__statistics = {
            ("ranks", lambda x: x.get_load()): {
                "maximum load": "maximum"},
            ("ranks", lambda x: self._work_model.compute(x)): {
                "total work": "sum"}}

    def get_initial_communications(self):
        """Return the initial phase communications."""
        return self._initial_communications

    def get_initial_phase(self):
        """Return initial phase."""
        return self._initial_phase

    def get_rebalanced_phase(self):
        """Return rebalanced phased."""
        return self._rebalanced_phase

    @staticmethod
    def factory(
        algorithm_name:str,
        parameters: dict,
        work_model: WorkModelBase,
        logger: Logger):
        """Instantiate the necessary concrete algorithm."""
        # Load up available algorithms
        # pylint:disable=W0641:possibly-unused-variable,C0415:import-outside-toplevel
        from .lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
        from .lbsBruteForceAlgorithm import BruteForceAlgorithm
        from .lbsPrescribedPermutationAlgorithm import PrescribedPermutationAlgorithm
        from .lbsPhaseStepperAlgorithm import PhaseStepperAlgorithm
        from .lbsCentralizedPrefixOptimizerAlgorithm import CentralizedPrefixOptimizerAlgorithm
        # pylint:enable=W0641:possibly-unused-variable,C0415:import-outside-toplevel

        # Ensure that algorithm name is valid
        try:
            # Instantiate and return object
            algorithm = locals()[algorithm_name + "Algorithm"]
            return algorithm(work_model, parameters, logger)
        except Exception as e:
            # Otherwise, error out
            logger.error(f"Could not create an algorithm with name {algorithm_name}")
            raise SystemExit(1) from e

    def _update_statistics(self, statistics: dict):
        """Compute and update run statistics."""
        # Create or update statistics dictionary entries
        for (support, getter), stat_names in self.__statistics.items():
            for k, v in stat_names.items():
                self._logger.debug(f"Updating {k} statistics for {support}")
                stats = compute_function_statistics(
                    getattr(self._rebalanced_phase, f"get_{support}")(), getter)
                statistics.setdefault(k, []).append(getattr(stats, f"get_{v}")())

    def _report_final_mapping(self, logger):
        """Report final rank object mapping in debug mode."""
        for rank in self._rebalanced_phase.get_ranks():
            logger.debug(f"Rank {rank.get_id()}:")
            for o in rank.get_objects():
                comm = o.get_communicator()
                if comm:
                    logger.debug(f"Object {o.get_id()}:")
                    recv = comm.get_received().items()
                    if recv:
                        logger.debug("received from:")
                        for k, v in recv:
                            logger.debug(
                                f"object {k.get_id()} on rank {k.get_rank_id()}: {v}")
                    sent = comm.get_sent().items()
                    if sent:
                        logger.debug("sent to:")
                        for k, v in sent:
                            logger.debug(
                                f"object {k.get_id()} on rank {k.get_rank_id()}: {v}")

    def _initialize(self, p_id, phases, statistics):
        """Factor out pre-execution checks and initalizations."""
        # Ensure that a list with at least one phase was provided
        if not isinstance(phases, dict) or not all(
            isinstance(p, Phase) for p in phases.values()):
            self._logger.error("Algorithm execution requires a dictionary of phases")
            raise SystemExit(1)

        # Try to retrieve and keep track of phase to be processed
        try:
            self._initial_phase = phases[p_id]
        except Exception as err:
            self._logger.error(f"No phase with index {p_id} is available for processing")
            raise SystemExit(1) from err
        self._initial_communications[p_id] = self._initial_phase.get_communications()

        # Create storage for rebalanced phase
        self._rebalanced_phase = Phase(self._logger, p_id)
        self._rebalanced_phase.copy_ranks(self._initial_phase)
        self._logger.info(
            f"Processing phase {p_id} "
            f"with {self._rebalanced_phase.get_number_of_objects()} objects "
            f"across {self._rebalanced_phase.get_number_of_ranks()} ranks "
            f"into phase {self._rebalanced_phase.get_id()}")

        # Replicate nodes on rebalanced phase
        ranks_per_node = 1
        new_nodes: List[Node] = []
        phase_ranks = self._initial_phase.get_ranks()
        if (nr := len(phase_ranks)) > 0 and phase_ranks[0].node is not None:
            ranks_per_node = phase_ranks[0].node.get_number_of_ranks()
            if ranks_per_node > 1:
                n_nodes = int(nr / ranks_per_node)
                new_nodes = list(map(
                    lambda n_id: Node(self._logger, n_id),
                    list(range(0, n_nodes))))

        # Initialize run statistics
        self._update_statistics(statistics)

    @abc.abstractmethod
    def execute(self, p_id, phases, statistics, a_min_max):
        """Execute balancing algorithm on Phase instance.

        :param: p_id: index of phase to be rebalanced (all if equal to _)
        :param: phases: list of Phase instances
        :param: statistics: dictionary of  statistics
        :param: a_min_max: possibly empty list of optimal arrangements.
        """
