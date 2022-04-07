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

from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsObjectCommunicator import ObjectCommunicator


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.sent_object = {Object(i=0, t=1.0): 6.0}
        self.received_object = {Object(i=1, t=2.5): 5.0}
        self.oc = ObjectCommunicator(i=123, r=self.received_object, s=self.sent_object, logger=self.logger)

    def test_object_communicator_initialization_001(self):
        self.assertEqual(self.oc._ObjectCommunicator__received, self.received_object)
        self.assertEqual(self.oc._ObjectCommunicator__sent, self.sent_object)
        self.assertEqual(self.oc._ObjectCommunicator__object_index, 123)

    def test_object_communicator_initialization_002(self):
        oc = ObjectCommunicator(i=133, logger=self.logger)
        self.assertEqual(oc._ObjectCommunicator__received, {})
        self.assertEqual(oc._ObjectCommunicator__sent, {})
        self.assertEqual(oc._ObjectCommunicator__object_index, 133)

    def test_object_communicator_get_received(self):
        self.assertEqual(self.oc.get_received(), self.received_object)

    def test_object_communicator_get_received_from_object(self):
        received_obj = list(self.sent_object.keys())[0]
        self.assertEqual(self.oc.get_received_from_object(received_obj), self.received_object.get(received_obj))

    def test_object_communicator_get_sent(self):
        self.assertEqual(self.oc.get_sent(), self.sent_object)

    def test_object_communicator_get_sent_to_object(self):
        sent_obj = list(self.sent_object.keys())[0]
        self.assertEqual(self.oc.get_sent_to_object(sent_obj), self.sent_object.get(sent_obj))

    def test_object_communicator_summarize_001(self):
        sent_objects = {Object(i=0, t=1.0): 2.0, Object(i=1, t=0.5): 1.0, Object(i=4, t=0.5): 2.0,
                        Object(i=3, t=0.5): 1.5}
        received_objects = {Object(i=5, t=2.0): 2.0, Object(i=6, t=0.5): 1.0, Object(i=2, t=0.5): 1.0,
                            Object(i=8, t=1.5): 0.5}
        oc_sum = ObjectCommunicator(i=154, r=received_objects, s=sent_objects, logger=self.logger)
        w_sent, w_recv = oc_sum.summarize()
        self.assertEqual(w_sent, [2.0, 1.0, 2.0, 1.5])
        self.assertEqual(w_recv, [2.0, 1.0, 1.0, 0.5])
        self.assertTrue(isinstance(w_sent, list))
        self.assertTrue(isinstance(w_recv, list))

    def test_object_communicator_summarize_002(self):
        w_sent, w_recv = self.oc.summarize()
        self.assertEqual(w_sent, [6.0])
        self.assertEqual(w_recv, [5.0])
        self.assertTrue(isinstance(w_sent, list))
        self.assertTrue(isinstance(w_recv, list))


if __name__ == '__main__':
    unittest.main()
