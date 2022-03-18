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
from src.Model.lbsObjectCommunicator import ObjectCommunicator


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.simple_obj_001 = Object(i=1, t=2.5)
        self.simple_obj_002 = Object(i=2, t=4.5, p=0)
        self.oc = ObjectCommunicator(logger=self.logger)
        self.simple_obj_003 = Object(i=3, t=3.5, p=2, c=self.oc)
        self.sent_objects = {Object(i=0, t=1.0): 2.0, Object(i=1, t=0.5): 1.0, Object(i=4, t=0.5): 2.0,
                             Object(i=3, t=0.5): 1.5}
        self.received_objects = {Object(i=5, t=2.0): 2.0, Object(i=6, t=0.5): 1.0, Object(i=2, t=0.5): 1.0,
                                 Object(i=8, t=1.5): 0.5}

    def test_object_initialization_001(self):
        self.assertEqual(self.simple_obj_001.index, 1)
        self.assertEqual(self.simple_obj_001.time, 2.5)
        self.assertEqual(self.simple_obj_001.rank_id, None)
        self.assertEqual(self.simple_obj_001.communicator, None)

    def test_object_initialization_002(self):
        self.assertEqual(self.simple_obj_002.index, 2)
        self.assertEqual(self.simple_obj_002.time, 4.5)
        self.assertEqual(self.simple_obj_002.rank_id, 0)
        self.assertEqual(self.simple_obj_002.communicator, None)

    def test_object_initialization_003(self):
        self.assertEqual(self.simple_obj_003.index, 3)
        self.assertEqual(self.simple_obj_003.time, 3.5)
        self.assertEqual(self.simple_obj_003.rank_id, 2)
        self.assertEqual(self.simple_obj_003.communicator, self.oc)

    def test_object_repr(self):
        self.assertEqual(str(self.simple_obj_001), 'Object id: 1, time: 2.5')
        self.assertEqual(str(self.simple_obj_002), 'Object id: 2, time: 4.5')
        self.assertEqual(str(self.simple_obj_003), 'Object id: 3, time: 3.5')

    def test_object_get_id(self):
        self.assertEqual(self.simple_obj_001.get_id(), 1)
        self.assertEqual(self.simple_obj_002.get_id(), 2)
        self.assertEqual(self.simple_obj_003.get_id(), 3)

    def test_object_get_time(self):
        self.assertEqual(self.simple_obj_001.get_time(), 2.5)
        self.assertEqual(self.simple_obj_002.get_time(), 4.5)
        self.assertEqual(self.simple_obj_003.get_time(), 3.5)

    def test_object_set_rank_id(self):
        self.simple_obj_001.set_rank_id(15)
        self.simple_obj_002.set_rank_id(24)
        self.simple_obj_003.set_rank_id(33)
        self.assertEqual(self.simple_obj_001.rank_id, 15)
        self.assertEqual(self.simple_obj_002.rank_id, 24)
        self.assertEqual(self.simple_obj_003.rank_id, 33)

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
            Object(i='25', t=2.5)
        self.assertEqual(err.exception.args[0], f"i: 25 is type of <class 'str'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=2.5, t=2.5)
        self.assertEqual(err.exception.args[0], f"i: 2.5 is type of <class 'float'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=True, t=2.5)
        self.assertEqual(err.exception.args[0], f"i: True is type of <class 'bool'>! Must be <class 'int'>!")

    def test_object_time_error(self):
        with self.assertRaises(TypeError) as err:
            Object(i=1, t='2.5')
        self.assertEqual(err.exception.args[0], f"t: 2.5 is type of <class 'str'>! Must be <class 'float'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=2, t=3)
        self.assertEqual(err.exception.args[0], f"t: 3 is type of <class 'int'>! Must be <class 'float'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=3, t=True)
        self.assertEqual(err.exception.args[0], f"t: True is type of <class 'bool'>! Must be <class 'float'>!")

    def test_object_rank_error(self):
        with self.assertRaises(TypeError) as err:
            Object(i=0, t=2.5, p='4')
        self.assertEqual(err.exception.args[0], f"p: 4 is type of <class 'str'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, t=5.5, p=4.0)
        self.assertEqual(err.exception.args[0], f"p: 4.0 is type of <class 'float'>! Must be <class 'int'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, t=5.5, p=True)
        self.assertEqual(err.exception.args[0], f"p: True is type of <class 'bool'>! Must be <class 'int'>!")

    def test_object_communicator_error(self):
        with self.assertRaises(TypeError) as err:
            Object(i=0, t=2.5, p=0, c='communicator')
        self.assertEqual(err.exception.args[0],
                         f"c: communicator is type of <class 'str'>! Must be <class 'ObjectCommunicator'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, t=5.5, p=1, c=4)
        self.assertEqual(err.exception.args[0], f"c: 4 is type of <class 'int'>! Must be <class 'ObjectCommunicator'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=2, t=4.5, p=2, c=4.0)
        self.assertEqual(err.exception.args[0],
                         f"c: 4.0 is type of <class 'float'>! Must be <class 'ObjectCommunicator'>!")

        with self.assertRaises(TypeError) as err:
            Object(i=1, t=5.5, p=1, c=True)
        self.assertEqual(err.exception.args[0],
                         f"c: True is type of <class 'bool'>! Must be <class 'ObjectCommunicator'>!")

    def test_object_has_communicator(self):
        self.assertTrue(self.simple_obj_003.has_communicator())
        self.assertFalse(self.simple_obj_002.has_communicator())

    def test_object_get_communicator(self):
        self.assertEqual(self.simple_obj_003.get_communicator(), self.oc)
        self.assertEqual(self.simple_obj_002.get_communicator(), None)

    def test_object_set_communicator(self):
        self.simple_obj_002.set_communicator(self.oc)
        self.assertEqual(self.simple_obj_002.communicator, self.oc)

    def test_object_set_communicator_get_communicator(self):
        self.simple_obj_002.set_communicator(self.oc)
        self.assertEqual(self.simple_obj_002.get_communicator(), self.oc)

    def test_object_get_sent_001(self):
        self.assertEqual(self.simple_obj_002.get_sent(), {})
        self.assertEqual(self.simple_obj_003.get_sent(), {})

    def test_object_get_sent_002(self):
        sent_object = {Object(i=0, t=1.0): 6.0}
        oc = ObjectCommunicator(s=sent_object, logger=self.logger)
        obj_with_comm = Object(i=3, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_sent(), sent_object)

    def test_object_get_sent_003(self):
        oc = ObjectCommunicator(s=self.sent_objects, logger=self.logger)
        obj_with_comm = Object(i=23, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_sent(), self.sent_objects)

    def test_object_get_received_001(self):
        self.assertEqual(self.simple_obj_002.get_received(), {})
        self.assertEqual(self.simple_obj_003.get_received(), {})

    def test_object_get_received_002(self):
        received_object = {Object(i=1, t=2.5): 5.0}
        oc = ObjectCommunicator(r=received_object, logger=self.logger)
        obj_with_comm = Object(i=3, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_received(), received_object)

    def test_object_get_received_003(self):
        oc = ObjectCommunicator(r=self.received_objects, logger=self.logger)
        obj_with_comm = Object(i=23, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_received(), self.received_objects)

    def test_object_get_sent_volume_001(self):
        self.assertEqual(self.simple_obj_002.get_sent_volume(), 0)
        self.assertEqual(self.simple_obj_003.get_sent_volume(), 0)

    def test_object_get_sent_volume_002(self):
        sent_object = {Object(i=0, t=1.0): 6.0}
        oc = ObjectCommunicator(s=sent_object, logger=self.logger)
        obj_with_comm = Object(i=3, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_sent_volume(), 6.0)

    def test_object_get_sent_volume_003(self):
        oc = ObjectCommunicator(s=self.sent_objects, logger=self.logger)
        obj_with_comm = Object(i=23, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_sent_volume(), 6.5)

    def test_object_get_received_volume_001(self):
        self.assertEqual(self.simple_obj_002.get_received_volume(), 0)
        self.assertEqual(self.simple_obj_003.get_received_volume(), 0)

    def test_object_get_received_volume_002(self):
        received_object = {Object(i=5, t=2.5): 7.0}
        oc = ObjectCommunicator(r=received_object, logger=self.logger)
        obj_with_comm = Object(i=3, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_received_volume(), 7.0)

    def test_object_get_received_volume_003(self):
        oc = ObjectCommunicator(r=self.received_objects, logger=self.logger)
        obj_with_comm = Object(i=23, t=3.5, p=2, c=oc)
        self.assertEqual(obj_with_comm.get_received_volume(), 4.5)


if __name__ == '__main__':
    unittest.main()