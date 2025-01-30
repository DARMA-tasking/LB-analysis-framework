#
#@HEADER
###############################################################################
#
#                              test_lbs_object.py
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
import unittest

from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsObjectCommunicator import ObjectCommunicator


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.subphases = [
            {"id": 0, "time": 1.3960000018187202e-06}, {"id": 1, "time": 3.2324999992283665e-05},
            {"id": 2, "time": 7.802999995476512e-06}, {"id": 3, "time": 0.00017973499998902298},
            {"id": 4, "time": 4.138999999980797e-05}, {"id": 5, "time": 0.0002490769999923259},
            {"id": 6, "time": 1.6039999977124353e-06}, {"id": 7, "time": 3.9705999995476304e-05},
            {"id": 8, "time": 1.5450000034888944e-06}, {"id": 9, "time": 5.735999998535135e-06},
            {"id": 10, "time": 0.00021168499999646428}, {"id": 11, "time": 0.0007852130000003399},
            {"id": 12, "time": 1.642999997386596e-06}, {"id": 13, "time": 3.634999998780586e-06}]
        self.simple_obj_001 = Object(seq_id=1, load=2.5, subphases=self.subphases)
        self.simple_obj_002 = Object(seq_id=2, load=4.5, r_id=0)
        self.oc = ObjectCommunicator(i=3, logger=self.logger)
        self.simple_obj_003 = Object(seq_id=3, load=3, r_id=2, comm=self.oc)
        self.sent_objects = {Object(seq_id=0, load=1.0): 2.0, Object(seq_id=1, load=0.5): 1.0, Object(seq_id=4, load=0.5): 2.0,
                             Object(seq_id=3, load=0.5): 1.5}
        self.received_objects = {Object(seq_id=5, load=2.0): 2.0, Object(seq_id=6, load=0.5): 1.0, Object(seq_id=2, load=0.5): 1.0,
                                 Object(seq_id=8, load=1.5): 0.5}

    def test_object_initialization_001(self):
        self.assertEqual(self.simple_obj_001._Object__seq_id, 1)
        self.assertEqual(self.simple_obj_001._Object__load, 2.5)
        self.assertEqual(self.simple_obj_001._Object__rank_id, None)
        self.assertEqual(self.simple_obj_001._Object__communicator, None)

    def test_object_initialization_002(self):
        self.assertEqual(self.simple_obj_002._Object__seq_id, 2)
        self.assertEqual(self.simple_obj_002._Object__load, 4.5)
        self.assertEqual(self.simple_obj_002._Object__rank_id, 0)
        self.assertEqual(self.simple_obj_002._Object__communicator, None)

    def test_object_initialization_003(self):
        self.assertEqual(self.simple_obj_003._Object__seq_id, 3)
        self.assertEqual(self.simple_obj_003._Object__load, 3.0)
        self.assertEqual(self.simple_obj_003._Object__rank_id, 2)
        self.assertEqual(self.simple_obj_003._Object__communicator, self.oc)

    def test_object_repr(self):
        self.assertEqual(str(self.simple_obj_001), "<Object id: 1, load: 2.5>")
        self.assertEqual(str(self.simple_obj_002), "<Object id: 2, load: 4.5>")
        self.assertEqual(str(self.simple_obj_003), "<Object id: 3, load: 3.0>")

    def test_object_get_id(self):
        self.assertEqual(self.simple_obj_001.get_id(), 1)
        self.assertEqual(self.simple_obj_002.get_id(), 2)
        self.assertEqual(self.simple_obj_003.get_id(), 3)

    def test_object_get_load(self):
        self.assertEqual(self.simple_obj_001.get_load(), 2.5)
        self.assertEqual(self.simple_obj_002.get_load(), 4.5)
        self.assertEqual(self.simple_obj_003.get_load(), 3.0)

    def test_object_set_rank_id(self):
        self.simple_obj_001.set_rank_id(15)
        self.simple_obj_002.set_rank_id(24)
        self.simple_obj_003.set_rank_id(33)
        self.assertEqual(self.simple_obj_001._Object__rank_id, 15)
        self.assertEqual(self.simple_obj_002._Object__rank_id, 24)
        self.assertEqual(self.simple_obj_003._Object__rank_id, 33)

    def test_object_get_rank_id(self):
        self.assertEqual(self.simple_obj_001.get_rank_id(), None)
        self.assertEqual(self.simple_obj_002.get_rank_id(), 0)
        self.assertEqual(self.simple_obj_003.get_rank_id(), 2)

    def test_object_set_rank_id_get_rank_id(self):
        self.simple_obj_001.set_rank_id(0)
        self.simple_obj_002.set_rank_id(3)
        self.simple_obj_003.set_rank_id(7)
        self.assertEqual(self.simple_obj_001.get_rank_id(), 0)
        self.assertEqual(self.simple_obj_002.get_rank_id(), 3)
        self.assertEqual(self.simple_obj_003.get_rank_id(), 7)

    def test_object_id_error(self):
        with self.assertRaises(TypeError) as err:
            Object(seq_id="25", load=2.5)
        self.assertEqual(err.exception.args[0], "seq_id: incorrect type <class 'str'>")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=2.5, load=2.5)
        self.assertEqual(err.exception.args[0], "seq_id: incorrect type <class 'float'>")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=True, load=2.5)
        self.assertEqual(err.exception.args[0], "seq_id: incorrect type <class 'bool'>")

    def test_object_load_error(self):
        with self.assertRaises(TypeError) as err:
            Object(seq_id=1, load="2.5")
        self.assertEqual(err.exception.args[0], "load: incorrect type <class 'str'> or value: 2.5")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=3, load=True)
        self.assertEqual(err.exception.args[0], "load: incorrect type <class 'bool'> or value: True")

    def test_object_rank_error(self):
        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id="4")
        self.assertEqual(err.exception.args[0], "r_id: incorrect type <class 'str'>")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=1, load=5.5, r_id=4.0)
        self.assertEqual(err.exception.args[0], "r_id: incorrect type <class 'float'>")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=1, load=5.5, r_id=True)
        self.assertEqual(err.exception.args[0], "r_id: incorrect type <class 'bool'>")

    def test_object_communicator_error(self):
        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm="communicator")
        self.assertEqual(err.exception.args[0], "comm: communicator is of type <class 'str'>. Must be <class 'ObjectCommunicator'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=1, load=5.5, r_id=1, comm=4)
        self.assertEqual(err.exception.args[0], "comm: 4 is of type <class 'int'>. Must be <class 'ObjectCommunicator'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=2, load=4.5, r_id=2, comm=4.0)
        self.assertEqual(err.exception.args[0], "comm: 4.0 is of type <class 'float'>. Must be <class 'ObjectCommunicator'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=1, load=5.5, r_id=1, comm=True)
        self.assertEqual(err.exception.args[0], "comm: True is of type <class 'bool'>. Must be <class 'ObjectCommunicator'>.")

    def test_object_user_defined_error(self):
        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm=self.oc, user_defined=[])
        self.assertEqual(err.exception.args[0], "user_defined: [] is of type <class 'list'>. Must be <class 'dict'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm=self.oc, user_defined='a')
        self.assertEqual(err.exception.args[0], "user_defined: a is of type <class 'str'>. Must be <class 'dict'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm=self.oc, user_defined=1)
        self.assertEqual(err.exception.args[0], "user_defined: 1 is of type <class 'int'>. Must be <class 'dict'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm=self.oc, user_defined=1.0)
        self.assertEqual(err.exception.args[0],
                         "user_defined: 1.0 is of type <class 'float'>. Must be <class 'dict'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm=self.oc, user_defined=set())
        self.assertEqual(err.exception.args[0],
                         "user_defined: set() is of type <class 'set'>. Must be <class 'dict'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm=self.oc, user_defined=())
        self.assertEqual(err.exception.args[0], "user_defined: () is of type <class 'tuple'>. Must be <class 'dict'>.")

        with self.assertRaises(TypeError) as err:
            Object(seq_id=0, load=2.5, r_id=0, comm=self.oc, user_defined=True)
        self.assertEqual(err.exception.args[0],
                         "user_defined: True is of type <class 'bool'>. Must be <class 'dict'>.")

    def test_object_has_communicator(self):
        self.assertTrue(self.simple_obj_003.has_communicator())
        self.assertFalse(self.simple_obj_002.has_communicator())

    def test_object_get_communicator(self):
        self.assertEqual(self.simple_obj_003.get_communicator(), self.oc)
        self.assertEqual(self.simple_obj_002.get_communicator(), None)

    def test_object_set_communicator(self):
        self.simple_obj_002.set_communicator(self.oc)
        self.assertEqual(self.simple_obj_002._Object__communicator, self.oc)

    def test_object_set_communicator_get_communicator(self):
        self.simple_obj_002.set_communicator(self.oc)
        self.assertEqual(self.simple_obj_002.get_communicator(), self.oc)

    def test_object_get_sent_001(self):
        self.assertEqual(self.simple_obj_002.get_sent(), {})
        self.assertEqual(self.simple_obj_003.get_sent(), {})

    def test_object_get_sent_002(self):
        sent_object = {Object(seq_id=0, load=1.0): 6.0}
        oc = ObjectCommunicator(i=3, s=sent_object, logger=self.logger)
        obj_with_comm = Object(seq_id=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent(), sent_object)

    def test_object_get_sent_003(self):
        oc = ObjectCommunicator(i=23, s=self.sent_objects, logger=self.logger)
        obj_with_comm = Object(seq_id=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent(), self.sent_objects)

    def test_object_get_received_001(self):
        self.assertEqual(self.simple_obj_002.get_received(), {})
        self.assertEqual(self.simple_obj_003.get_received(), {})

    def test_object_get_received_002(self):
        received_object = {Object(seq_id=1, load=2.5): 5.0}
        oc = ObjectCommunicator(i=1, r=received_object, logger=self.logger)
        obj_with_comm = Object(seq_id=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received(), received_object)

    def test_object_get_received_003(self):
        oc = ObjectCommunicator(i=23, r=self.received_objects, logger=self.logger)
        obj_with_comm = Object(seq_id=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received(), self.received_objects)

    def test_object_get_sent_volume_001(self):
        self.assertEqual(self.simple_obj_002.get_sent_volume(), 0)
        self.assertEqual(self.simple_obj_003.get_sent_volume(), 0)

    def test_object_get_sent_volume_002(self):
        sent_object = {Object(seq_id=0, load=1.0): 6.0}
        oc = ObjectCommunicator(i=3, s=sent_object, logger=self.logger)
        obj_with_comm = Object(seq_id=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent_volume(), 6.0)

    def test_object_get_sent_volume_003(self):
        oc = ObjectCommunicator(i=23, s=self.sent_objects, logger=self.logger)
        obj_with_comm = Object(seq_id=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent_volume(), 6.5)

    def test_object_get_received_volume_001(self):
        self.assertEqual(self.simple_obj_002.get_received_volume(), 0)
        self.assertEqual(self.simple_obj_003.get_received_volume(), 0)

    def test_object_get_received_volume_002(self):
        received_object = {Object(seq_id=5, load=2.5): 7.0}
        oc = ObjectCommunicator(i=3, r=received_object, logger=self.logger)
        obj_with_comm = Object(seq_id=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received_volume(), 7.0)

    def test_object_get_received_volume_003(self):
        oc = ObjectCommunicator(i=23, r=self.received_objects, logger=self.logger)
        obj_with_comm = Object(seq_id=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received_volume(), 4.5)

    def test_object_get_subphases(self):
        self.assertEqual(self.simple_obj_001.get_subphases(), self.subphases)
        self.assertEqual(self.simple_obj_002.get_subphases(), None)


if __name__ == "__main__":
    unittest.main()
