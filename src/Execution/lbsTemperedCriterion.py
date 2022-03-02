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
import sys
import copy

from logging import Logger

from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsObjectCommunicator import ObjectCommunicator
from src.Model.lbsRank import Rank


class TemperedCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6
    """

    def __init__(self, work_model, parameters: dict = None, lgr: Logger = None):
        """Class constructor
        work_model: WorkModel instante
        parameters: optional parameters dictionary
        """

        # Call superclass init
        super(TemperedCriterion, self).__init__(work_model, parameters)

        # Assign logger to instance variable
        self.lgr = lgr
        self.lgr.info("Instantiated concrete criterion")

        # Determine how destination load is to be computed
        def get_dst_load_know_by_src(p_src, p_dst):
            return p_src.get_known_loads()[p_dst]

        def get_actual_dst_load(_, p_dst):
            return p_dst.get_load()

        # Retrieve relevant parameter when available
        self.dst_load = get_dst_load_know_by_src if not (parameters and parameters.get("actual_destination_load")) \
            else get_actual_dst_load

    def compute(self, objects: list, p_src: Rank, p_dst: Rank) -> float:
        """Tempered work criterion based on L1 norm of works
        """

        # Compute original arrangement works
        values_src = {
            "load": p_src.get_load(),
            "received volume": p_src.get_received_volume(),
            "sent volume": p_src.get_sent_volume()}
        w_src_0 = self.work_model.aggregate(values_src)
        values_dst = {
            "load": p_dst.get_load(),
            "received volume": p_dst.get_received_volume(),
            "sent volume": p_dst.get_sent_volume()}
        w_dst_0 = self.work_model.aggregate(values_dst)
        w_max_0 = max(w_src_0, w_dst_0)

        # Update loads in proposed new arrangement
        object_loads = sum([o.get_time() for o in objects])
        values_src["load"] -= object_loads
        values_dst["load"] += object_loads

        # Retrieve IDs of source and destination ranks
        src_id = p_src.get_id()
        dst_id = p_dst.get_id()

        # Update communication volumes
        v_src_to_src = 0.
        v_src_to_dst = 0.
        v_src_to_oth = 0.
        v_src_from_src = 0.
        v_src_from_dst = 0.
        v_src_from_oth = 0.
        for o in objects:
            # Skip objects without a communicator
            comm = o.get_communicator()
            if not isinstance(comm, ObjectCommunicator):
                continue

            # Retrieve items not sent nor received from object list
            recv = {(k, v) for k, v in comm.get_received().items()
                    if k not in objects}
            sent = {(k, v) for k, v in comm.get_sent().items()
                    if k not in objects}

            # Tally sent communication volumes by destination
            for k, v in sent:
                if k.get_rank_id() == src_id:
                    v_src_to_src += v
                elif k.get_rank_id() == dst_id:
                    v_src_to_dst += v
                else:
                    v_src_to_oth += v

            # Tally received communication volumes by source
            for k, v in recv:
                if k.get_rank_id() == src_id:
                    v_src_from_src += v
                elif k.get_rank_id() == dst_id:
                    v_src_from_dst += v
                else:
                    v_src_from_oth += v

        # Update volumes by transferring non-local communications
        values_src["sent volume"] -= v_src_to_dst + v_src_to_oth
        values_dst["sent volume"] += v_src_to_src + v_src_to_oth
        values_src["received volume"] -= v_src_from_dst + v_src_from_oth
        values_dst["received volume"] += v_src_from_src + v_src_from_oth

        # Swap sent/recieved volumes for local commmunications
        values_src["sent volume"] += v_src_from_src
        values_dst["sent volume"] -= v_src_from_dst 
        values_src["received volume"] += v_src_to_src
        values_dst["received volume"] -= v_src_to_dst

        # Compute proposed new arrangement works
        w_src_new = self.work_model.aggregate(values_src)
        w_dst_new = self.work_model.aggregate(values_dst)
        w_max_new = max(w_src_new, w_dst_new)

        # Return criterion value
        return w_max_0 - w_max_new
