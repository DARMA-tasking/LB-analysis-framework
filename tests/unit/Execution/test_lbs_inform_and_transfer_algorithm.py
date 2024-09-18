#
#@HEADER
###############################################################################
#
#                  test_lbs_inform_and_transfer_algorithm.py
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
import logging
import random
import unittest
from unittest.mock import patch

from src.lbaf.Model.lbsMessage import Message
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Execution.lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.migratable_objects = {Object(seq_id=0, load=1.0), Object(seq_id=1, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=3, load=0.5)}
        self.sentinel_objects = {Object(seq_id=15, load=4.5), Object(seq_id=18, load=2.5)}
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
        self.work_model = WorkModelBase.factory(
            work_name="AffineCombination",
            parameters={},
            lgr=self.logger)
        self.inform_and_transfer = InformAndTransferAlgorithm(
            work_model=self.work_model,
            parameters={
                "n_iterations": 8,
                "n_rounds": 4,
                "fanout": 4,
                "order_strategy": "element_id",
                "transfer_strategy": "Recursive",
                "criterion": "Tempered",
                "max_subclusters": 15,
                "max_objects_per_transfer": 8,
                "deterministic_transfer": True
            },
            lgr=self.logger,
            rank_qoi=None,
            object_qoi=None)

    @patch.object(random, "sample")
    def test_lbs_inform_and_transfer_forward_message(self, random_mock):
        temp_rank_1 = Rank(r_id=1, logger=self.logger)
        temp_rank_2 = Rank(r_id=2, logger=self.logger)
        random_mock.return_value = [temp_rank_1, temp_rank_2]

        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r_snd=self.rank,
                f=4)[0],
            [temp_rank_1, temp_rank_2]
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r_snd=self.rank,
                f=4)[1].get_round(),
            Message(2, {"loads": self.inform_and_transfer.get_known_peers()}).get_round()
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r_snd=self.rank,
                f=4)[1].get_support(),
            Message(2, self.inform_and_transfer.get_known_peers()[self.rank]).get_support()
        )
    def test_lbs_inform_and_transfer_process_message(self):
        temp_rank_1 = Rank(r_id=1, logger=self.logger)
        self.inform_and_transfer._InformAndTransferAlgorithm__process_message(
            self.rank, Message(1,{temp_rank_1: 4.0})
        )
        known_peers = self.inform_and_transfer.get_known_peers()
        self.assertEqual(known_peers, {self.rank: {self.rank, temp_rank_1}})

if __name__ == "__main__":
    unittest.main()