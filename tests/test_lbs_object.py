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
        self.simple_obj_001 = Object(i=1, load=2.5, subphases=self.subphases)
        self.simple_obj_002 = Object(i=2, load=4.5, r_id=0)
        self.oc = ObjectCommunicator(i=3, logger=self.logger)
        self.simple_obj_003 = Object(i=3, load=3.5, r_id=2, comm=self.oc)
        self.sent_objects = {Object(i=0, load=1.0): 2.0, Object(i=1, load=0.5): 1.0, Object(i=4, load=0.5): 2.0,
                             Object(i=3, load=0.5): 1.5}
        self.received_objects = {Object(i=5, load=2.0): 2.0, Object(i=6, load=0.5): 1.0, Object(i=2, load=0.5): 1.0,
                                 Object(i=8, load=1.5): 0.5}

    def test_object_initialization_001(self):
        self.assertEqual(self.simple_obj_001._Object__index, 1)
        self.assertEqual(self.simple_obj_001._Object__load, 2.5)
        self.assertEqual(self.simple_obj_001._Object__rank_id, None)
        self.assertEqual(self.simple_obj_001._Object__communicator, None)

    def test_object_initialization_002(self):
        self.assertEqual(self.simple_obj_002._Object__index, 2)
        self.assertEqual(self.simple_obj_002._Object__load, 4.5)
        self.assertEqual(self.simple_obj_002._Object__rank_id, 0)
        self.assertEqual(self.simple_obj_002._Object__communicator, None)

    def test_object_initialization_003(self):
        self.assertEqual(self.simple_obj_003._Object__index, 3)
        self.assertEqual(self.simple_obj_003._Object__load, 3.5)
        self.assertEqual(self.simple_obj_003._Object__rank_id, 2)
        self.assertEqual(self.simple_obj_003._Object__communicator, self.oc)

    def test_object_repr(self):
        self.assertEqual(str(self.simple_obj_001), "Object id: 1, load: 2.5")
        self.assertEqual(str(self.simple_obj_002), "Object id: 2, load: 4.5")
        self.assertEqual(str(self.simple_obj_003), "Object id: 3, load: 3.5")

    def test_object_get_id(self):
        self.assertEqual(self.simple_obj_001.get_id(), 1)
        self.assertEqual(self.simple_obj_002.get_id(), 2)
        self.assertEqual(self.simple_obj_003.get_id(), 3)

    def test_object_get_load(self):
        self.assertEqual(self.simple_obj_001.get_load(), 2.5)
        self.assertEqual(self.simple_obj_002.get_load(), 4.5)
        self.assertEqual(self.simple_obj_003.get_load(), 3.5)

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
            Object(i="25", load=2.5)
        self.assertEqual(err.exception.args[0], f"i: 25 is type of <class 'str'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=2.5, load=2.5)
        self.assertEqual(err.exception.args[0], f"i: 2.5 is type of <class 'float'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=True, load=2.5)
        self.assertEqual(err.exception.args[0], f"i: True is type of <class 'bool'>! Must be <class 'int'>!")

    def test_object_load_error(self):
        with self.assertRaises(TypeError) as err:
            Object(i=1, load="2.5")
        self.assertEqual(err.exception.args[0], f"t: 2.5 is type of <class 'str'>! Must be <class 'float'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=2, load=3)
        self.assertEqual(err.exception.args[0], f"t: 3 is type of <class 'int'>! Must be <class 'float'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=3, load=True)
        self.assertEqual(err.exception.args[0], f"t: True is type of <class 'bool'>! Must be <class 'float'>!")

    def test_object_rank_error(self):
        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id="4")
        self.assertEqual(err.exception.args[0], f"p: 4 is type of <class 'str'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, load=5.5, r_id=4.0)
        self.assertEqual(err.exception.args[0], f"p: 4.0 is type of <class 'float'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, load=5.5, r_id=True)
        self.assertEqual(err.exception.args[0], f"p: True is type of <class 'bool'>! Must be <class 'int'>!")

    def test_object_communicator_error(self):
        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm="communicator")
        self.assertEqual(err.exception.args[0],
                         f"c: communicator is type of <class 'str'>! Must be <class 'ObjectCommunicator'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, load=5.5, r_id=1, comm=4)
        self.assertEqual(err.exception.args[0], f"c: 4 is type of <class 'int'>! Must be <class 'ObjectCommunicator'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=2, load=4.5, r_id=2, comm=4.0)
        self.assertEqual(err.exception.args[0],
                         f"c: 4.0 is type of <class 'float'>! Must be <class 'ObjectCommunicator'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, load=5.5, r_id=1, comm=True)
        self.assertEqual(err.exception.args[0],
                         f"c: True is type of <class 'bool'>! Must be <class 'ObjectCommunicator'>!")

    def test_object_user_defined_error(self):
        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm=self.oc, user_defined=[])
        self.assertEqual(err.exception.args[0],
                         f"user_defined: [] is type of <class 'list'>! Must be <class 'dict'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm=self.oc, user_defined="a")
        self.assertEqual(err.exception.args[0], f"user_defined: a is type of <class 'str'>! Must be <class 'dict'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm=self.oc, user_defined=1)
        self.assertEqual(err.exception.args[0], f"user_defined: 1 is type of <class 'int'>! Must be <class 'dict'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm=self.oc, user_defined=1.0)
        self.assertEqual(err.exception.args[0],
                         f"user_defined: 1.0 is type of <class 'float'>! Must be <class 'dict'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm=self.oc, user_defined=set())
        self.assertEqual(err.exception.args[0],
                         f"user_defined: set() is type of <class 'set'>! Must be <class 'dict'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm=self.oc, user_defined=())
        self.assertEqual(err.exception.args[0], f"user_defined: () is type of <class 'tuple'>! Must be <class 'dict'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=0, load=2.5, r_id=0, comm=self.oc, user_defined=True)
        self.assertEqual(err.exception.args[0],
                         f"user_defined: True is type of <class 'bool'>! Must be <class 'dict'>!")

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
        sent_object = {Object(i=0, load=1.0): 6.0}
        oc = ObjectCommunicator(i=3, s=sent_object, logger=self.logger)
        obj_with_comm = Object(i=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent(), sent_object)

    def test_object_get_sent_003(self):
        oc = ObjectCommunicator(i=23, s=self.sent_objects, logger=self.logger)
        obj_with_comm = Object(i=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent(), self.sent_objects)

    def test_object_get_received_001(self):
        self.assertEqual(self.simple_obj_002.get_received(), {})
        self.assertEqual(self.simple_obj_003.get_received(), {})

    def test_object_get_received_002(self):
        received_object = {Object(i=1, load=2.5): 5.0}
        oc = ObjectCommunicator(i=1, r=received_object, logger=self.logger)
        obj_with_comm = Object(i=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received(), received_object)

    def test_object_get_received_003(self):
        oc = ObjectCommunicator(i=23, r=self.received_objects, logger=self.logger)
        obj_with_comm = Object(i=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received(), self.received_objects)

    def test_object_get_sent_volume_001(self):
        self.assertEqual(self.simple_obj_002.get_sent_volume(), 0)
        self.assertEqual(self.simple_obj_003.get_sent_volume(), 0)

    def test_object_get_sent_volume_002(self):
        sent_object = {Object(i=0, load=1.0): 6.0}
        oc = ObjectCommunicator(i=3, s=sent_object, logger=self.logger)
        obj_with_comm = Object(i=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent_volume(), 6.0)

    def test_object_get_sent_volume_003(self):
        oc = ObjectCommunicator(i=23, s=self.sent_objects, logger=self.logger)
        obj_with_comm = Object(i=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_sent_volume(), 6.5)

    def test_object_get_received_volume_001(self):
        self.assertEqual(self.simple_obj_002.get_received_volume(), 0)
        self.assertEqual(self.simple_obj_003.get_received_volume(), 0)

    def test_object_get_received_volume_002(self):
        received_object = {Object(i=5, load=2.5): 7.0}
        oc = ObjectCommunicator(i=3, r=received_object, logger=self.logger)
        obj_with_comm = Object(i=3, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received_volume(), 7.0)

    def test_object_get_received_volume_003(self):
        oc = ObjectCommunicator(i=23, r=self.received_objects, logger=self.logger)
        obj_with_comm = Object(i=23, load=3.5, r_id=2, comm=oc)
        self.assertEqual(obj_with_comm.get_received_volume(), 4.5)

    def test_object_get_subphases(self):
        self.assertEqual(self.simple_obj_001.get_subphases(), self.subphases)
        self.assertEqual(self.simple_obj_002.get_subphases(), None)


if __name__ == "__main__":
    unittest.main()
