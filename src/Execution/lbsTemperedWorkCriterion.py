#
#@HEADER
###############################################################################
#
#                       lbsTemperedWorkCriterion.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
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
########################################################################
import bcolors

from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsObject import Object
from src.Model.lbsRank import Rank


class TemperedWorkCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6
    """

    def __init__(self, _, parameters):
        """Class constructor
        """

        # Call superclass init
        super(TemperedWorkCriterion, self).__init__(parameters)
        print(f"{bcolors.HEADER}[TemperedWorkCriterion]{bcolors.END} Instantiated concrete criterion")

        # Determine how destination work is to be computed
        self.dst_work = (
            lambda x: self.get_work(x) if parameters.get("actual_destination_work")) else (
            lambda x: p_src.get_known_work(x))
            

    def compute(self, obj: Object, p_src: Rank, p_dst: Rank) -> float:
        """Tempered work criterion based on L1 norm of works
        """

        # Criterion only uses object and rank works
        return self.get_work(p_src) - (self.dst_work(p_dst) + obj.get_time())