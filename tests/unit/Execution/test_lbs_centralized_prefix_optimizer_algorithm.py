#
#@HEADER
###############################################################################
#
#              test_lbs_centralized_prefix_optimizer_algorithm.py
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
import random
import unittest
from unittest.mock import patch

from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsBlock import Block
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase
from src.lbaf.IO.lbsStatistics import compute_function_statistics
from src.lbaf.Execution.lbsCentralizedPrefixOptimizerAlgorithm import CentralizedPrefixOptimizerAlgorithm


class TestConfig(unittest.TestCase):
    def setUp(self):

        # Set up logger
        self.logger = logging.getLogger()

        # Initialize inputs
        work_model = WorkModelBase.factory(
            work_name="AffineCombination",
            parameters={},
            lgr=self.logger)
        parameters = {"do_second_stage": True}

        # Create CPOA instance
        self.cpoa = CentralizedPrefixOptimizerAlgorithm(
            work_model=work_model,
            parameters=parameters,
            lgr=self.logger)

        # Set up phase
        self.sentinel_objects = {Object(seq_id=15, load=4.5), Object(seq_id=18, load=2.5)}
        self.migratable_objects = {Object(seq_id=0, load=1.0), Object(seq_id=1, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=3, load=0.5)}
        self.rank = Rank(r_id=0, logger=self.logger, migratable_objects=self.migratable_objects, sentinel_objects=self.sentinel_objects)
        self.phase = Phase(lgr=self.logger, p_id=0)
        self.phase.set_ranks([self.rank])

        # Create a shared block
        self.block = Block(b_id=0, h_id=0)
        for o in self.migratable_objects:
            o.set_shared_block(self.block)

        # Create dict of phase(s)
        self.phases = {self.phase.get_id(): self.phase}

        # Set up statistics
        l_stats = compute_function_statistics(
            self.phase.get_ranks(),
            lambda x: x.get_load())
        self.statistics = {"average load": l_stats.get_average()}

    def test_lbs_cpoa_execute(self):
        self.cpoa.execute(
            self.phase.get_id(),
            self.phases,
            self.statistics)
        new_phase = self.cpoa.get_rebalanced_phase()
        self.assertEqual(
            new_phase.get_id(),
            self.phase.get_id())

if __name__ == "__main__":
    unittest.main()
