#
#@HEADER
###############################################################################
#
#                           lbsTemperedCriterion.py
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
from typing import Optional

from .lbsCriterionBase import CriterionBase
from ..Model.lbsRank import Rank


class TemperedCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6."""

    def __init__(self, work_model, lgr: Logger):
        """Class constructor."""
        # Call superclass init
        super().__init__(work_model, lgr)
        self._logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, r_src: Rank, o_src: list, r_dst: Rank, o_dst: Optional[list]=None) -> float:
        """Tempered work criterion based on L1 norm of works."""
        if o_dst is None:
            o_dst = []

        # Compute maximum work of original arrangement
        w_max_0 = max(
            self._work_model.compute(r_src),
            self._work_model.compute(r_dst))

        # Move objects into proposed new arrangement
        self._phase.transfer_objects(r_src, o_src, r_dst, o_dst)

        # Compute maximum work of proposed new arrangement
        w_max_new = max(
            self._work_model.compute(r_src),
            self._work_model.compute(r_dst))

        # Move objects back into original arrangement
        self._phase.transfer_objects(r_dst, o_src, r_src, o_dst)

        # Return criterion value
        return w_max_0 - w_max_new
