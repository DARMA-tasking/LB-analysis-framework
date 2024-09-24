#
#@HEADER
###############################################################################
#
#                       test_lbs_object_communicator.py
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
        self.sent_object = {Object(seq_id=0, load=1.0): 6.0}
        self.received_object = {Object(seq_id=1, load=2.5): 5.0}
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
        sent_objects = {
            Object(seq_id=0, load=1.0): 2.0,
            Object(seq_id=1, load=0.5): 1.0,
            Object(seq_id=4, load=0.5): 2.0,
            Object(seq_id=3, load=0.5): 1.5}
        received_objects = {
            Object(seq_id=5, load=2.0): 2.0,
            Object(seq_id=6, load=0.5): 1.0,
            Object(seq_id=2, load=0.5): 1.0,
            Object(seq_id=8, load=1.5): 0.5}
        oc_sum = ObjectCommunicator(
            i=154, r=received_objects, s=sent_objects, logger=self.logger)
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

    def test_object_communicator_summarize_exception_003(self):
        sent_objects = {
            Object(seq_id=154, load=1.0): 2.0,
            Object(seq_id=1, load=0.5): 1.0,
            Object(seq_id=4, load=0.5): 2.0,
            Object(seq_id=3, load=0.5): 1.5}
        received_objects = {
            Object(seq_id=5, load=2.0): 2.0,
            Object(seq_id=6, load=0.5): 1.0,
            Object(seq_id=2, load=0.5): 1.0,
            Object(seq_id=8, load=1.5): 0.5}
        oc_sum = ObjectCommunicator(
            i=154, r=received_objects, s=sent_objects, logger=self.logger)
        with self.assertRaises(IndexError) as err:
            w_sent, w_recv = oc_sum.summarize()
        self.assertEqual(
            err.exception.args[0], "object 154 cannot send communication to itself.")


if __name__ == "__main__":
    unittest.main()
