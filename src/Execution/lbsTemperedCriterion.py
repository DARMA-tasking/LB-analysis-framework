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
from logging import Logger

from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsObject import Object
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
        self.dst_load = get_dst_load_know_by_src if not (
            parameters and parameters.get(
                "actual_destination_load")) else get_actual_dst_load

    def compute(self, obj: Object, p_src: Rank, p_dst: Rank) -> float:
        """Tempered work criterion based on L1 norm of works
        """
        # Initialize storage for work aggregation
        values = {}

        # Compute load-based criterion
        values["load"] = self.dst_load(
            p_src, p_dst) + obj.get_time() - p_src.get_load()

        # Retrieve object communications
        comm = obj.get_communicator()
        if isinstance(comm, ObjectCommunicator):
            # Retrieve sent and received items from communicator
            recv = comm.get_received().items()
            sent = comm.get_sent().items()

            # Retrieve IDs of source and destination ranks
            src_id = p_src.get_id()
            dst_id = p_dst.get_id()

            # Aggregate communication volumes between source and destination
            v_recv_dst = sum([v for k, v in recv if k.get_rank_id() == dst_id])
            v_sent_dst = sum([v for k, v in sent if k.get_rank_id() == dst_id])

            # Aggregate communication volumes local to source
            v_recv_src = sum([v for k, v in recv if k.get_rank_id() == src_id])
            v_sent_src = sum([v for k, v in sent if k.get_rank_id() == src_id])

            # Compute differences between sent and received volumes
            values["received volume"] = v_recv_src - v_recv_dst
            values["sent volume"] = v_sent_src - v_sent_dst

        # Return aggregated criterion
        return - self.work_model.aggregate(values)
