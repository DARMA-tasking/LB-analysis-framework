#
#@HEADER
###############################################################################
#
#                             test_lbs_runtime.py
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
import os
import logging
import unittest

from src.lbaf.Execution.lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase
from src.lbaf.Execution.lbsRuntime import Runtime
from src.lbaf import PROJECT_PATH
from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsAffineCombinationWorkModel import AffineCombinationWorkModel
from src.lbaf.IO.lbsStatistics import compute_min_max_arrangements_work


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.test_dir, "data")
        self.logger = logging.getLogger()
        self.file_prefix = os.path.join(self.data_dir, "synthetic-blocks", "synthetic-dataset-blocks")
        self.reader = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix="json")
        self.phase = Phase(self.logger, 0, reader=self.reader)

        # Initialize inputs to Runtime class
        self.phases={}
        phase = Phase(
            self.logger, 0, reader=self.reader)
        phase.populate_from_log(0)
        self.phases[0] = phase
        self.work_model = {
            "name": "AffineCombination",
        }
        self.algorithm = {
            "name": "InformAndTransfer",
            "parameters": {
                "n_iterations": 8,
                "n_rounds": 4,
                "fanout": 4,
                "order_strategy": "element_id",
                "transfer_strategy": "Recursive",
                "criterion": "Tempered",
                "max_objects_per_transfer": 8,
                "deterministic_transfer": True
            }
        }
        objects = phase.get_objects()
        beta = 1.0
        gamma = 0.0
        n_ranks = 4

        # Initialize the Runtime instances
        self.runtime = Runtime(
            self.phases,
            self.work_model,
            self.algorithm,
            self.logger)

    def test_lbs_runtime_get_work_model(self):
        self.assertEqual(self.runtime.get_work_model().__class__, AffineCombinationWorkModel)

    def test_lbs_runtime_no_phases(self):
        with self.assertRaises(SystemExit) as context:
            runtime = Runtime(
                None,
                self.work_model,
                self.algorithm,
                self.logger)
        self.assertEqual(context.exception.code, 1)

    def test_lbs_runtime_execute(self):
        # Ensure execute method works as expected
        p_id = 0  # Provide a valid phase ID
        rebalanced_phase = self.runtime.execute(p_id)
        # Add assertions to check if the execute method behaves as expected
        assert rebalanced_phase is not None

if __name__ == "__main__":
    unittest.main()
