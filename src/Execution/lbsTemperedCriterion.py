#
#@HEADER
###############################################################################
#
#                       lbsTemperedCriterion.py
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
import functools

from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsObject import Object
from src.Model.lbsRank import Rank
from src.Model.lbsObjectCommunicator import ObjectCommunicator


class TemperedCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6
    """

    def __init__(self, work_model, parameters: dict):
        """Class constructor
        parameters: optional parameters dictionary
        """

        # Call superclass init
        super(TemperedCriterion, self).__init__(work_model, parameters)
        print(f"{bcolors.HEADER}[TemperedCriterion]{bcolors.END} Instantiated concrete criterion")

        
        # Determine how destination work is to be computed
        def get_dst_work_know_by_src(p_src, p_dst):
            return p_src.get_known_work(p_dst)
        def get_actual_dst_work(_, p_dst):
            return self.get_work(p_dst)

        # Retrieve releavant parameter when available
        self.dst_work = get_dst_work_know_by_src if not (
            parameters and parameters.get(
                "actual_destination_work")) else get_actual_dst_work

        self.alpha = 0.
        self.beta = 1.

    def compute(self, obj: Object, p_src: Rank, p_dst: Rank) -> float:
        """Tempered work criterion based on L1 norm of works
        """

        # Initialize criterion with comparison between object loads
        criterion = self.get_work(p_src) - (
            self.dst_work(p_src, p_dst) + self.alpha * obj.get_time())
        criterion = 0.
        # Retrieve object communications
        comm = obj.get_communicator()
        if isinstance(comm, ObjectCommunicator):
            # Retrieve sent and received items from communicator
            recv = comm.get_received().items()
            sent = comm.get_sent().items()

            # Retrieve IDs of source and destination ranks
            src_id = p_src.get_id()
            dst_id = p_dst.get_id()

            # Aggregate communication volumes local to source
            v_recv_src = sum([v for k, v in recv if k.get_rank_id() == src_id])
            v_sent_src = sum([v for k, v in sent if k.get_rank_id() == src_id])

            # Aggregate communication volumes between source and destination
            v_recv_dst = sum([v for k, v in recv if k.get_rank_id() == dst_id])
            v_sent_dst = sum([v for k, v in sent if k.get_rank_id() == dst_id])

            v_recv = v_recv_dst - v_recv_src
            if v_recv < 0.:
                criterion += v_recv
            v_sent = v_sent_dst - v_sent_src
            if v_sent < 0.:
                criterion += v_sent
            return -1.

            # Update criterion with volume differences
            #criterion += self.beta * min(v_recv, v_sent)

        # Criterion assesses difference in total work
        return criterion
