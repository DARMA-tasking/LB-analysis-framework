#
#@HEADER
###############################################################################
#
#                              test_lbs_phase.py
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

from src.lbaf import PROJECT_PATH
from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsPhase import Phase


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.test_dir, "data")
        self.logger = logging.getLogger()
        self.file_prefix = os.path.join(self.data_dir, "synthetic-blocks", "synthetic-dataset-blocks")
        self.reader = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix="json")
        self.phase = Phase(self.logger, 0, reader=self.reader)

    def test_lbs_phase_initialization(self):
        self.assertEqual(self.phase._Phase__ranks, [])
        self.assertEqual(self.phase._Phase__phase_id, 0)
        self.assertEqual(self.phase._Phase__edges, None)

    def test_lbs_phase_populate_from_log(self):
        file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_compressed", "data")
        self.phase.populate_from_log(0)
        self.assertEqual(len(self.phase.get_object_ids()), 9)

    def test_lbs_phase_getters(self):
        file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_compressed", "data")
        self.phase.populate_from_log(0)
        ranks = sorted([rank.get_id() for rank in self.phase.get_ranks()])
        self.assertEqual(ranks, [0, 1, 2, 3])
        self.assertEqual(sorted(self.phase.get_rank_ids()), [0, 1, 2, 3])
        self.assertEqual(self.phase.get_id(), 0)

    def test_lbs_phase_edges(self):
        file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_compressed", "data")
        self.phase.populate_from_log(0)
        self.assertEqual(self.phase._Phase__edges, None)
        edges = {frozenset({0, 1}): 3.0, frozenset({0, 2}): 0.5, frozenset({1, 2}): 2.0}
        self.assertEqual(self.phase.get_edge_maxima(), edges)

    def test_lbs_phase_populate_from_samplers(self):
        t_sampler = {"name": "lognormal", "parameters": [1.0, 10.0]}
        v_sampler = {"name": "lognormal", "parameters": [1.0, 10.0]}

        self.phase.populate_from_samplers(
            n_ranks=4, n_objects=200,
            t_sampler=t_sampler, v_sampler=v_sampler,
            c_degree=20, n_r_mapped=4)
        for rank in self.phase.get_ranks():
            self.assertTrue(rank.get_migratable_objects())
        self.assertEqual(self.phase._Phase__edges, None)
        edges = self.phase.get_edge_maxima()
        self.assertEqual(len(edges), 6)
        expected_edges = [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]
        self.assertEqual(sorted([list(edge) for edge in edges]), expected_edges)


if __name__ == "__main__":
    unittest.main()
