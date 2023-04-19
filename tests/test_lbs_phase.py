import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

import logging
import unittest

from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsPhase import Phase


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            raise SystemExit(1)
        self.logger = logging.getLogger()
        self.file_prefix = os.path.join(self.data_dir, 'synthetic_lb_data_compressed', 'data')
        self.reader = LoadReader(file_prefix=self.file_prefix, n_ranks=4, logger=self.logger, file_suffix='json')
        self.phase = Phase(self.logger, 0, reader=self.reader)

    def test_lbs_phase_initialization(self):
        self.assertEqual(self.phase._Phase__ranks, [])
        self.assertEqual(self.phase._Phase__phase_id, 0)
        self.assertEqual(self.phase._Phase__edges, None)

    def test_lbs_phase_populate_from_log(self):
        file_prefix = os.path.join(self.data_dir, 'synthetic_lb_data_compressed', 'data')
        self.phase.populate_from_log(t_s=0, basename=file_prefix)
        self.assertEqual(len(self.phase.get_object_ids()), 9)

    def test_lbs_phase_getters(self):
        file_prefix = os.path.join(self.data_dir, 'synthetic_lb_data_compressed', 'data')
        self.phase.populate_from_log(t_s=0, basename=file_prefix)
        ranks = sorted([rank.get_id() for rank in self.phase.get_ranks()])
        self.assertEqual(ranks, [0, 1, 2, 3])
        self.assertEqual(sorted(self.phase.get_rank_ids()), [0, 1, 2, 3])
        self.assertEqual(self.phase.get_id(), 0)

    def test_lbs_phase_edges(self):
        file_prefix = os.path.join(self.data_dir, 'synthetic_lb_data_compressed', 'data')
        self.phase.populate_from_log(t_s=0, basename=file_prefix)
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
