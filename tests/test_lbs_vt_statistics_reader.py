import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    exit(1)

import logging
import unittest

from src.IO.lbsVTStatisticsReader import LoadReader


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            exit(1)
        file_prefix = os.path.join(self.data_dir, 'synthetic_lb_stats', 'stats')
        logger = logging.getLogger()
        self.lr = LoadReader(file_prefix=file_prefix, logger=logger, file_suffix='json')

    def test_get_node_trace_file_name_001(self):
        file_name = f"{self.lr.file_prefix}.0.{self.lr.file_suffix}"
        self.assertEqual(file_name, self.lr.get_node_trace_file_name(node_id=0))

    def test_get_node_trace_file_name_002(self):
        file_name = f"{self.lr.file_prefix}.100.{self.lr.file_suffix}"
        self.assertEqual(file_name, self.lr.get_node_trace_file_name(node_id=100))

    def test_get_node_trace_file_name_003(self):
        # Node_id is an in 000 is converted to 0
        file_name = f"{self.lr.file_prefix}.000.{self.lr.file_suffix}"
        self.assertNotEqual(file_name, self.lr.get_node_trace_file_name(node_id=000))

    def test_read(self):
        # TODO: Add rank_iter_map
        ranks_comm = [
            {
                5: {'sent': [], 'received': [{'from': 0, 'bytes': 2.0}]},
                0: {'sent': [{'to': 5, 'bytes': 2.0}], 'received': []},
                4: {'sent': [], 'received': [{'from': 1, 'bytes': 1.0}]},
                1: {'sent': [{'to': 4, 'bytes': 1.0}], 'received': []},
                2: {'sent': [], 'received': [{'from': 3, 'bytes': 1.0}]},
                3: {'sent': [{'to': 2, 'bytes': 1.0}, {'to': 8, 'bytes': 0.5}], 'received': []},
                8: {'sent': [], 'received': [{'from': 3, 'bytes': 0.5}]}},
            {
                1: {'sent': [], 'received': [{'from': 4, 'bytes': 2.0}]},
                4: {'sent': [{'to': 1, 'bytes': 2.0}], 'received': []},
                8: {'sent': [], 'received': [{'from': 5, 'bytes': 2.0}]},
                5: {'sent': [{'to': 8, 'bytes': 2.0}], 'received': []},
                6: {'sent': [], 'received': [{'from': 7, 'bytes': 1.0}]},
                7: {'sent': [{'to': 6, 'bytes': 1.0}], 'received': []}},
            {
                6: {'sent': [], 'received': [{'from': 8, 'bytes': 1.5}]},
                8: {'sent': [{'to': 6, 'bytes': 1.5}], 'received': []}},
            {}
        ]
        for phase in range(4):
            rank_iter_map, rank_comm = self.lr.read(phase, 0)
            self.assertEqual(ranks_comm[phase], rank_comm)


if __name__ == '__main__':
    unittest.main()
