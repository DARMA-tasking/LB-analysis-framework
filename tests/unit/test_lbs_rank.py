import logging
import random
import unittest
from unittest.mock import patch

from lbaf.Model.lbsMessage import Message
from lbaf.Model.lbsObject import Object
from lbaf.Model.lbsObjectCommunicator import ObjectCommunicator
from lbaf.Model.lbsRank import Rank


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.migratable_objects = {Object(i=0, load=1.0), Object(i=1, load=0.5), Object(i=2, load=0.5), Object(i=3, load=0.5)}
        self.sentinel_objects = {Object(i=15, load=4.5), Object(i=18, load=2.5)}
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)

    def test_lbs_rank_initialization(self):
        self.assertEqual(self.rank._Rank__index, 0)
        self.assertEqual(self.rank._Rank__migratable_objects, self.migratable_objects)
        self.assertEqual(self.rank._Rank__known_loads, {})
        self.assertEqual(self.rank._Rank__sentinel_objects, self.sentinel_objects)

    def test_lbs_rank_repr(self):
        self.assertEqual(self.rank.__repr__(), "<Rank index: 0>")

    def test_lbs_rank_get_id(self):
        self.assertEqual(self.rank.get_id(), 0)

    def test_lbs_rank_get_objects(self):
        self.assertEqual(self.rank.get_objects(), self.migratable_objects.union(self.sentinel_objects))

    def test_lbs_rank_add_migratable_object(self):
        temp_object = Object(i=7, load=1.5)
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

    def test_lbs_rank_get_load(self):
        self.assertEqual(self.rank.get_load(), 9.5)

    def test_lbs_rank_get_migratable_load(self):
        self.assertEqual(self.rank.get_migratable_load(), 2.5)

    def test_lbs_rank_get_sentinel_load(self):
        self.assertEqual(self.rank.get_sentinel_load(), 7.0)

    def test_lbs_rank_get_received_volume_001(self):
        sent_objects = {Object(i=123, load=1.0): 2.0, Object(i=1, load=0.5): 1.0, Object(i=4, load=0.5): 2.0,
                        Object(i=3, load=0.5): 1.5}
        received_objects = {Object(i=5, load=2.0): 2.0, Object(i=6, load=0.5): 1.0, Object(i=2, load=0.5): 1.0,
                            Object(i=8, load=1.5): 0.5}
        oc = ObjectCommunicator(i=154, r=received_objects, s=sent_objects, logger=self.logger)
        temp_mig_object = Object(i=123, load=1.0, comm=oc)
        self.rank.add_migratable_object(temp_mig_object)
        self.assertEqual(self.rank.get_received_volume(), 4.5)

    def test_lbs_rank_get_sent_volume_001(self):
        sent_objects = {Object(i=123, load=1.0): 2.0, Object(i=1, load=0.5): 1.0, Object(i=4, load=0.5): 2.0,
                        Object(i=3, load=0.5): 1.5}
        received_objects = {Object(i=5, load=2.0): 2.0, Object(i=6, load=0.5): 1.0, Object(i=2, load=0.5): 1.0,
                            Object(i=8, load=1.5): 0.5}
        oc = ObjectCommunicator(i=154, r=received_objects, s=sent_objects, logger=self.logger)
        temp_mig_object = Object(i=123, load=1.0, comm=oc)
        self.rank.add_migratable_object(temp_mig_object)
        self.assertEqual(self.rank.get_sent_volume(), 6.5)

    def test_lbs_rank_remove_migratable_object(self):
        temp_rank = Rank(r_id=1, logger=self.logger)
        temp_object = Object(i=7, load=1.5)
        self.rank.add_migratable_object(temp_object)
        self.migratable_objects.add(temp_object)
        self.assertEqual(self.rank.get_migratable_objects(), self.migratable_objects)
        self.rank._Rank__known_loads[temp_rank] = 4.0
        self.rank.remove_migratable_object(temp_object, temp_rank)
        self.migratable_objects.remove(temp_object)
        self.assertEqual(self.rank.get_migratable_objects(), self.migratable_objects)

    def test_lbs_rank_reset_all_load_information(self):
        temp_rank = Rank(r_id=1, logger=self.logger)
        self.rank._Rank__known_loads[temp_rank] = 4.0
        self.assertEqual(self.rank.get_known_loads(), {temp_rank: 4.0})
        self.rank.reset_all_load_information()
        self.assertEqual(self.rank.get_known_loads(), {})

if __name__ == "__main__":
    unittest.main()
