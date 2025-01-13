#
#@HEADER
###############################################################################
#
#                               test_lbs_rank.py
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

from src.lbaf.Model.lbsMessage import Message
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsObjectCommunicator import ObjectCommunicator
from src.lbaf.Model.lbsRank import Rank


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.migratable_objects = {Object(seq_id=0, load=1.0), Object(seq_id=1, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=3, load=0.5)}
        self.sentinel_objects = {Object(seq_id=15, load=4.5), Object(seq_id=18, load=2.5)}
        self.rank = Rank(r_id=0, migratable_objects=self.migratable_objects, sentinel_objects=self.sentinel_objects, logger=self.logger)

    def test_lbs_rank_initialization(self):
        self.assertEqual(self.rank._Rank__index, 0)
        self.assertEqual(self.rank._Rank__migratable_objects, self.migratable_objects)
        self.assertEqual(self.rank._Rank__sentinel_objects, self.sentinel_objects)

    def test_lbs_rank_repr(self):
        self.assertEqual(self.rank.__repr__(), "<Rank index: 0, node: None>")

    def test_lbs_rank_get_id(self):
        self.assertEqual(self.rank.get_id(), 0)

    def test_lbs_rank_get_objects(self):
        self.assertEqual(self.rank.get_objects(), self.migratable_objects.union(self.sentinel_objects))

    def test_lbs_rank_add_migratable_object(self):
        temp_object = Object(seq_id=7, load=1.5)
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

    def test_lbs_rank_get_load(self):
        self.assertEqual(self.rank.get_load(), 9.5)

    def test_lbs_rank_get_migratable_load(self):
        self.assertEqual(self.rank.get_migratable_load(), 2.5)

    def test_lbs_rank_get_sentinel_load(self):
        self.assertEqual(self.rank.get_sentinel_load(), 7.0)

    def test_lbs_rank_set_size(self):
        self.rank.set_size(3.0)
        self.assertEqual(self.rank.get_size(), 3.0)
        self.rank.set_size(3)
        self.assertEqual(self.rank.get_size(), 3.0)
        with self.assertRaises(TypeError) as err:
            self.rank.set_size(True)
        self.assertEqual(err.exception.args[0], "size: incorrect type <class 'bool'> or value: True")

    def test_lbs_rank_get_received_volume_001(self):
        sent_objects = {Object(seq_id=123, load=1.0): 2.0, Object(seq_id=1, load=0.5): 1.0, Object(seq_id=4, load=0.5): 2.0,
                        Object(seq_id=3, load=0.5): 1.5}
        received_objects = {Object(seq_id=5, load=2.0): 2.0, Object(seq_id=6, load=0.5): 1.0, Object(seq_id=2, load=0.5): 1.0,
                            Object(seq_id=8, load=1.5): 0.5}
        oc = ObjectCommunicator(i=154, r=received_objects, s=sent_objects, logger=self.logger)
        temp_mig_object = Object(seq_id=123, load=1.0, comm=oc)
        self.rank.add_migratable_object(temp_mig_object)
        self.assertEqual(self.rank.get_received_volume(), 4.5)

    def test_lbs_rank_get_sent_volume_001(self):
        sent_objects = {Object(seq_id=123, load=1.0): 2.0, Object(seq_id=1, load=0.5): 1.0, Object(seq_id=4, load=0.5): 2.0,
                        Object(seq_id=3, load=0.5): 1.5}
        received_objects = {Object(seq_id=5, load=2.0): 2.0, Object(seq_id=6, load=0.5): 1.0, Object(seq_id=2, load=0.5): 1.0,
                            Object(seq_id=8, load=1.5): 0.5}
        oc = ObjectCommunicator(i=154, r=received_objects, s=sent_objects, logger=self.logger)
        temp_mig_object = Object(seq_id=123, load=1.0, comm=oc)
        self.rank.add_migratable_object(temp_mig_object)
        self.assertEqual(self.rank.get_sent_volume(), 6.5)

    def test_lbs_rank_remove_migratable_object(self):
        temp_rank = Rank(r_id=1, logger=self.logger)
        temp_object = Object(seq_id=7, load=1.5)
        self.rank.add_migratable_object(temp_object)
        self.migratable_objects.add(temp_object)
        self.assertEqual(self.rank.get_migratable_objects(), self.migratable_objects)
        self.rank.remove_migratable_object(temp_object)
        self.migratable_objects.remove(temp_object)
        self.assertEqual(self.rank.get_migratable_objects(), self.migratable_objects)

if __name__ == "__main__":
    unittest.main()
