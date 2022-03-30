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

from src.Model.lbsObject import Object
from src.Model.lbsRank import Rank


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.migratable_objects = {Object(i=0, t=1.0), Object(i=1, t=0.5), Object(i=2, t=0.5), Object(i=3, t=0.5)}
        self.sentinel_objects = {Object(i=15, t=4.5), Object(i=18, t=2.5)}
        self.rank = Rank(i=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)

    def test_lbs_rank_initialization(self):
        self.assertEqual(self.rank._Rank__index, 0)
        self.assertEqual(self.rank._Rank__migratable_objects, self.migratable_objects)
        self.assertEqual(self.rank._Rank__known_loads, {})
        self.assertEqual(self.rank._Rank__viewers, set())
        self.assertEqual(self.rank.round_last_received, 0)
        self.assertEqual(self.rank._Rank__sentinel_objects, self.sentinel_objects)

    def test_lbs_rank_repr(self):
        self.assertEqual(self.rank.__repr__(), '<Rank index: 0>')

    def test_lbs_rank_get_id(self):
        self.assertEqual(self.rank.get_id(), 0)

    def test_lbs_rank_get_objects(self):
        self.assertEqual(self.rank.get_objects(), self.migratable_objects.union(self.sentinel_objects))

    def test_lbs_rank_add_migratable_object(self):
        temp_object = Object(i=7, t=1.5)
        self.rank.add_migratable_object(temp_object)
        self.migratable_objects.add(temp_object)
        self.assertEqual(self.rank.get_migratable_objects(), self.migratable_objects)

    def test_lbs_rank_get_migratable_objects(self):
        self.assertEqual(self.rank.get_migratable_objects(), self.migratable_objects)

    def test_lbs_rank_get_sentinel_objects(self):
        self.assertEqual(self.rank.get_sentinel_objects(), self.sentinel_objects)

    def test_lbs_rank_get_object_ids(self):
        self.assertEqual(sorted(self.rank.get_object_ids()), [0, 1, 2, 3, 15, 18])

    def test_lbs_rank_get_migratable_object_ids(self):
        self.assertEqual(sorted(self.rank.get_migratable_object_ids()), [0, 1, 2, 3])

    def test_lbs_rank_get_sentinel_object_ids(self):
        self.assertEqual(sorted(self.rank.get_sentinel_object_ids()), [15, 18])

    def test_lbs_rank_get_known_loads(self):
        self.assertEqual(self.rank.get_known_loads(), {})

    def test_lbs_rank_get_viewers(self):
        self.assertEqual(self.rank.get_viewers(), set())

    def test_lbs_rank_get_load(self):
        self.assertEqual(self.rank.get_load(), 9.5)

    def test_lbs_rank_get_migratable_load(self):
        self.assertEqual(self.rank.get_migratable_load(), 2.5)

    def test_lbs_rank_get_sentinel_load(self):
        self.assertEqual(self.rank.get_sentinel_load(), 7.0)

    def test_lbs_rank_get_received_volume_001(self):
        self.assertEqual(self.rank.get_received_volume(), 0.0)

    def test_lbs_rank_get_sent_volume_001(self):
        self.assertEqual(self.rank.get_sent_volume(), 0.0)


if __name__ == '__main__':
    unittest.main()
