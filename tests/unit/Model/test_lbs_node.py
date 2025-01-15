#
#@HEADER
###############################################################################
#
#                               test_lbs_node.py
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
import logging
import unittest

from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsNode import Node


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.node_id = 0
        self.ranks = set()
        self.rank_ids = set(i for i in range(10))
        self.node = Node(logger=self.logger, n_id=self.node_id)

    def test_lbs_node_get_id(self):
        self.assertEqual(self.node.get_id(), self.node_id)

    def test_lbs_node_max_memory_usage(self):
        phase = Phase(lgr=self.logger, p_id=0)
        phase_ranks = set()
        all_migratable_objs = set()

        obj_size = 1.0
        num_objs = len(self.rank_ids)

        for rank_id in self.rank_ids:
            obj = Object(
                seq_id=rank_id,
                r_id=rank_id,
                size=obj_size,
            )
            rank = Rank(
                logger=self.logger,
                r_id=rank_id,
                migratable_objects={obj})
            self.ranks.add(rank)
            rank.set_node(self.node)
            
            all_migratable_objs.add(obj)
            phase_ranks.add(rank)

        phase.set_ranks(phase_ranks)
        self.assertEqual(
            self.node.get_max_memory_usage(phase),
            obj_size * num_objs
        )
