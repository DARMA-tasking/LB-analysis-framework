#
#@HEADER
###############################################################################
#
#                   test_lbs_recursive_transfer_strategy.py
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
import os
import sys
import logging
import unittest

from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsBlock import Block
from src.lbaf.Model.lbsObject import Object
from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase
from src.lbaf.Execution.lbsCriterionBase import CriterionBase
from src.lbaf.Model.lbsObjectCommunicator import ObjectCommunicator
from src.lbaf.Execution.lbsRecursiveTransferStrategy import RecursiveTransferStrategy


class TestConfig(unittest.TestCase):
    def setUp(self):
        #Instantiate the logger
        self.logger = logging.getLogger()

        self.params = {"order_strategy":"increasing_loads"}

        # Define the work model and criterion
        self.work_model = WorkModelBase.factory(
            "AffineCombination",
            self.params,
            self.logger)
        self.criterion = CriterionBase.factory(
            "Tempered",
            self.work_model,
            self.logger)

        # Define objects and add them to a memory block
        self.migratable_objects = {Object(seq_id=0, load=1.0), Object(seq_id=1, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=3, load=0.5)}
        self.sentinel_objects = {Object(seq_id=15, load=4.5), Object(seq_id=18, load=2.5)}
        self.block = Block(b_id=0,h_id=0)
        self.block_set = {self.block}
        for o in self.migratable_objects:
          o.set_shared_block(self.block)
          self.block.attach_object_id(o.get_id())

        # Define the rank and declare known peers
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
        self.rank.set_shared_blocks(self.block_set)
        self.known_peers = {}

        # Instantiate the phase
        self.phase = Phase(self.logger)
        self.phase.set_ranks([self.rank])
        self.criterion.set_phase(self.phase)

        # Finally, create instance of Recursive Transfer Strategy
        self.recursive_transfer_strategy=RecursiveTransferStrategy(criterion=self.criterion, parameters=self.params, logger=self.logger)

    def test_recursive_transfer_strategy_orderings(self):

        # Define all order strategies
        order_strategy_list = ["arbitrary", "element_id", "decreasing_loads",
                               "increasing_loads", "fewest_migrations", "small_objects"]

        # Initialize empty parameter dict
        param_dict = {}

        # Set up received and sent objects
        rec_object_min = {Object(seq_id=7, load=0.5): 5.0}
        rec_object_max = {Object(seq_id=8, load=1.0): 10.0}
        sent_object_min = {Object(seq_id=9, load=0.5): 6.0}
        sent_object_max = {Object(seq_id=10, load=1.0): 12.0}

        # Create objects
        obj_04 = Object(seq_id=4, load=5.0, comm=ObjectCommunicator(i=4,logger=self.logger,r=rec_object_max, s=sent_object_max))
        obj_05 = Object(seq_id=5, load=3.0, comm=ObjectCommunicator(i=5,logger=self.logger,r=rec_object_min, s=sent_object_min))
        obj_06 = Object(seq_id=6, comm=None)

        # Define objects set
        objects = [
          obj_04,
          obj_05,
          obj_06
        ]

        # Set expected orders
        expected_order_dict = {
            "arbitrary": objects,
            "element_id": objects,
            "decreasing_loads": objects,
            "increasing_loads": objects[::-1],
            "fewest_migrations": objects,
            "small_objects": objects
        }

        # Test every order strategy
        for order_strategy in order_strategy_list:
            param_dict["order_strategy"] = order_strategy
            recursive_strat = RecursiveTransferStrategy(criterion=self.criterion, parameters=param_dict, logger=self.logger)
            self.assertEqual(f"{order_strategy}: {getattr(recursive_strat, order_strategy)(objects, 0)}",
                             f"{order_strategy}: {expected_order_dict[order_strategy]}")

if __name__ == "__main__":
    unittest.main()
