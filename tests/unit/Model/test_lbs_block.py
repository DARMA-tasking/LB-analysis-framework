#
#@HEADER
###############################################################################
#
#                              test_lbs_block.py
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
import unittest
from unittest.mock import patch

from src.lbaf.Model.lbsBlock import Block


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Set up input parameters
        self.b_id = 0
        self.h_id = 0
        self.size = 1.0
        self.o_ids = {0,1,2,3,4}

        # Create Block instance
        self.block = Block(self.b_id, self.h_id, self.size, self.o_ids)

    def test_lbs_block_initialization(self):
        wrong_sizes = [1, -1.0]
        for wrong_size in wrong_sizes:
            with self.assertRaises(TypeError) as err:
                block_wrong_size = Block(b_id=1, h_id=1, size=wrong_size)
            self.assertEqual(str(err.exception), f"size: incorrect type {type(wrong_size)} or value: {wrong_size}")

        wrong_oids = {0:0, 1:1, 2:2, 3:3}
        with self.assertRaises(TypeError) as err:
            block_wrong_oid = Block(b_id=1, h_id=1, o_ids=wrong_oids)
        self.assertEqual(str(err.exception), f"o_ids: incorrect type {type(wrong_oids)}")

    def test_lbs_block_repr(self):
        self.assertEqual(
            repr(self.block),
            f"Block id: {self.block.get_id()}, home id: {self.h_id}, size: {self.size}, object ids: {self.o_ids}"
        )

    def test_lbs_block_detach_object_id(self):
        wrong_oid = 57
        with self.assertRaises(TypeError) as err:
            self.block.detach_object_id(o_id=57)
        self.assertEqual(str(err.exception), f"object id {wrong_oid} is not attached to block {self.block.get_id()}")

if __name__ == "__main__":
    unittest.main()
