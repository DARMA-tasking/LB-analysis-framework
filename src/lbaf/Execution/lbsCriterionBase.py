#
#@HEADER
###############################################################################
#
#                             lbsCriterionBase.py
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
from logging import Logger
from typing import List, Optional

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Model.lbsPhase import Phase
from ..Utils.lbsLogging import get_logger

class CriterionBase:
    """An abstract base class of optimization criteria for LBAF execution."""
    __metaclass__ = abc.ABCMeta

    # Protected logger
    _logger: Logger

    def __init__(self, work_model: WorkModelBase, logger: Logger):
        """Class constructor:
            work_model: a WorkModelBase instance
            phase: a Phase instance
            logger: Logger instance."""

        # Assign logger to instance variable
        self._logger = logger
        logger.debug(
            f"Creating base criterion with {str(type(work_model)).rsplit('.', maxsplit=1)[-1][:-2]} work model")

        # Assert that a work model instance was passed
        if not isinstance(work_model, WorkModelBase):
            self._logger.error("Could not create a criterion without a work model")
            raise SystemExit(1)
        self._work_model = work_model

        # No phase is initially assigned
        self._phase = None

    def set_phase(self, phase: Phase):
        """Assign phase to criterion to provide access to phase methods."""

        # Assert that a phase instance was passed
        if not isinstance(phase, Phase):
            self._logger.error(f"A {type(phase)} instance was passed to set_phase()")
            raise SystemExit(1)
        self._phase = phase

    @staticmethod
    def factory(criterion_name: str, work_model: WorkModelBase, logger: Logger):
        """Produce the necessary concrete criterion."""

        # Load up available criteria
        # pylint:disable=W0641:possibly-unused-variable,C0415:import-outside-toplevel
        from .lbsTemperedCriterion import TemperedCriterion
        from .lbsStrictLocalizingCriterion import StrictLocalizingCriterion
        # pylint:enable=W0641:possibly-unused-variable,C0415:import-outside-toplevel

        # Ensure that criterion name is valid
        try:
            # Instantiate and return object
            criterion = locals()[criterion_name + "Criterion"]
            return criterion(work_model, logger)
        except Exception as e:
            # Otherwise, error out
            get_logger().error(f"Could not create a criterion with name {criterion_name}")
            raise SystemExit(1) from e

    @abc.abstractmethod
    def compute(self, r_src, o_src, r_dst, o_dst: Optional[List]=None):
        """Compute value of criterion for candidate objects transfer

        :param r_src: iterable of objects on source
        :param o_src: Rank instance
        :param r_dst: Rank instance
        :param o_dst: optional iterable of objects on destination for swaps.
        """
        # Must be implemented by concrete subclass
