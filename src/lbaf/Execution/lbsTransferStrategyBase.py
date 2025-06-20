#
#@HEADER
###############################################################################
#
#                          lbsTransferStrategyBase.py
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
import math
import random
from logging import Logger

from ..IO.lbsStatistics import inverse_transform_sample
from ..Execution.lbsCriterionBase import CriterionBase
from ..Utils.lbsLogging import get_logger


class TransferStrategyBase:
    """An abstract base class of transfer strategies for inform and transfer algorithm."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, criterion, parameters: dict, logger: Logger):
        """Class constructor.

        :param criterion: a CriterionBase instance
        :param parameters: a dictionary of parameters
        :param logger: a Logger instance.
        """
        # Assert that a logger instance was passed
        if not isinstance(logger, Logger):
            get_logger().error(f"Incorrect type {type(logger)} passed instead of Logger instance")
            raise SystemExit(1)
        self._logger = logger

        # Assert that a criterion base instance was passed
        if not isinstance(criterion, CriterionBase):
            self._logger.error("Could not create a transfer strategy without a criterion")
            raise SystemExit(1)
        self._criterion = criterion

        # Assign optional parameters
        self._max_objects_per_transfer = parameters.get("max_objects_per_transfer", math.inf)
        self._deterministic_transfer = parameters.get("deterministic_transfer", False)
        logger.info(
            f"Created {'' if self._deterministic_transfer else 'non'}deterministic transfer strategy, "
            f"max. {self._max_objects_per_transfer} objects")

        # Null defaut value for average load
        self._average_load = 0.0

        # Initialize numbers of transfers and rejects
        self._n_transfers = 0
        self._n_rejects = 0

    def _initialize_transfer_stage(self, ave_load: float):
        """Initialize transfer stage consistently across strategies."""

        # Keep track of average load
        self._logger.info(f"Executing transfer phase with average load: {ave_load}")
        self._average_load = ave_load

        # Initialize numbers of transfers and rejects
        self._n_transfers = 0
        self._n_rejects = 0

    def _get_ranks_to_traverse(self, ranks: list, known_peers: dict) -> dict:
        """Prepare randomized dict of ranks to transfer targets."""

        # Initialize dictionary of traversable ranks to targets
        rank_targets = {}

        # Iterate over all provided ranks
        for r_src in ranks:
            # Ignore ranks without migratable objects
            if not r_src.get_migratable_objects():
                continue

            # Retrieve potential targets
            targets = known_peers.get(r_src, set()).difference({r_src})
            if not targets:
                continue

            # Append rank to be traversed
            rank_targets[r_src] = targets

        # Return randomized dict of rank_targets ranks
        return rank_targets if self._deterministic_transfer else {
            k: rank_targets[k]
            for k in random.sample(list(rank_targets.keys()), len(rank_targets))}

    def _randomly_select_target(self, r_src, objects: list, targets: set, strict=False):
        """Pseudo-randomly select transfer destination using ECMF."""
        # Initialize criterion values
        c_values = {}
        c_min, c_max = math.inf, -math.inf

        # Iterate over potential targets
        for r_dst in targets:
            # Compute value of criterion for current target
            c_dst = self._criterion.compute(r_src, objects, r_dst)

            # Do not include rejected targets for strict CMF
            if strict and c_dst < 0.:
                continue

            # Update criterion values
            c_values[r_dst] = c_dst
            c_min = min(c_min, c_dst)
            c_max = max(c_max, c_dst)

        # Initialize CMF depending on singleton or non-singleton support
        if c_min == c_max:
            # Sample uniformly if all criteria have same value
            cmf = {k: 1.0 / len(c_values) for k in c_values}
        else:
            # Otherwise, use relative weights
            c_range = c_max - c_min
            cmf = {k: (v - c_min) / c_range for k, v in c_values.items()}

        # Bail out early when no CMF can be computed
        if not cmf:
            return None, None

        # Compute cumlates
        sum_p = 0.0
        for k, v in cmf.items():
            sum_p += v
            cmf[k] = sum_p

        # Normalize cumulates to obtain CMF and criterion values
        for k, v in cmf.items():
            cmf[k] /= sum_p
        self._logger.debug(f"CMF = {cmf}")

        # Return selected target and corresponding criterion value
        r_dst = inverse_transform_sample(cmf)
        return r_dst, c_values[r_dst]

    @staticmethod
    def factory(
            strategy_name: str,
            parameters: dict,
            criterion: CriterionBase,
            logger: Logger):
        """Instantiate the necessary concrete strategy."""
        # Load up available strategies
        # pylint:disable=C0415:import-outside-toplevel,W0641:possibly-unused-variable
        from .lbsRecursiveTransferStrategy import RecursiveTransferStrategy
        from .lbsClusteringTransferStrategy import ClusteringTransferStrategy
        # pylint:enable=C0415:import-outside-toplevel,W0641:possibly-unused-variable

        # Ensure that strategy name is valid
        try:
            # Instantiate and return object
            strategy = locals()[strategy_name + "TransferStrategy"]
            return strategy(criterion, parameters, logger)
        except Exception as error:
            # Otherwise, error out
            get_logger().error(f"Could not create a strategy with name {strategy_name}")
            raise SystemExit(1) from error

    @abc.abstractmethod
    def execute(self, known_peers: dict, phase, ave_load: float, max_load: float):
        """Execute transfer strategy on Phase instance
        :param known_peers: a dictionary of sets of known rank peers
        :param phase: a Phase instance
        :param ave_load: average load in current phase.
        :param max_load: maximum load across current phase.
        """
        # Must be implemented by concrete subclass
