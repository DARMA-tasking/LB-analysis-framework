#
#@HEADER
###############################################################################
#
#                      test_lbs_brute_force_algorithm.py
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
from src.lbaf.Execution.lbsBruteForceAlgorithm import BruteForceAlgorithm
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase

class TestConfig(unittest.TestCase):
  def setUp(self):
    self.logger = logging.getLogger()
    # self.migratable_objects = {Object(seq_id=0, load=1.0), Object(seq_id=1, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=3, load=0.5)}
    # self.sentinel_objects = {Object(seq_id=15, load=4.5), Object(seq_id=18, load=2.5)}
    # self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
    self.brute_force_skip_transfer = BruteForceAlgorithm(
        work_model=WorkModelBase(),
        parameters={
            "n_iterations": 8,
            "n_rounds": 4,
            "fanout": 4,
            "order_strategy": "arbitrary",
            "criterion": "Tempered",
            "skip_transfer": True,
            "max_objects_per_transfer": 8,
            "deterministic_transfer": True
        },
        lgr=self.logger,
        rank_qoi=None,
        object_qoi=None)

    self.brute_force = BruteForceAlgorithm(
        work_model=WorkModelBase(),
        parameters={
            "n_iterations": 8,
            "n_rounds": 4,
            "fanout": 4,
            "order_strategy": "arbitrary",
            "criterion": "Tempered",
            "max_objects_per_transfer": 8,
            "deterministic_transfer": True
        },
        lgr=self.logger,
        rank_qoi=None,
        object_qoi=None)

  def test_lbs_brute_force_skip_transfer(self):
    assert self.brute_force_skip_transfer._BruteForceAlgorithm__skip_transfer is True

  # Test execute function

if __name__ == "__main__":
    unittest.main()
