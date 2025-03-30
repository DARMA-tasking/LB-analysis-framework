#
#@HEADER
###############################################################################
#
#                       lbsStrictLocalizingCriterion.py
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
from typing import List

from .lbsCriterionBase import CriterionBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsObject import Object
from ..Model.lbsRank import Rank


class StrictLocalizingCriterion(CriterionBase):
    """A concrete class for a strictly localizing criterion."""

    def __init__(self, workmodel, lgr):
        """Class constructor."""
        # Call superclass init
        super().__init__(workmodel, lgr)
        self._logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, r_src: Rank, o_src: List[Object], *_args) -> float:
        """A criterion enforcing strict conservation of local communications."""
        # Keep track source processor ID
        r_src_id = r_src.get_id()

        # Iterate over objects proposed for transfer
        for o in o_src:
            # Retrieve object communications
            comm = o.get_communicator()

            # Ignore object if it does not have a communicator
            if not isinstance(comm, ObjectCommunicator):
                continue

            # Iterate over sent messages
            for i in comm.get_sent().items():
                if r_src_id == i[0].get_rank_id():
                    # Bail out as soon as locality is broken by transfer
                    return -1.

            # Iterate over received messages
            for i in comm.get_received().items():
                if r_src_id == i[0].get_rank_id():
                    # Bail out as soon as locality is broken by transfer
                    return -1.

        # Accept transfer if this point was reached as no locality was broken
        return 1.
