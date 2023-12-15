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
        wrong_bid = 1.0
        with self.assertRaises(TypeError) as err:
            block_wrong_bid = Block(b_id=wrong_bid, h_id=1)
        self.assertEqual(str(err.exception), f"b_id: incorrect type {type(wrong_bid)}")

        wrong_hid = 1.0
        with self.assertRaises(TypeError) as err:
            block_wrong_hid = Block(b_id=1, h_id=wrong_hid)
        self.assertEqual(str(err.exception), f"h_id: incorrect type {type(wrong_hid)}")

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
            f"Block id: {self.__index}, home id: {self.__home_id}, size: {self.__size}, object ids: {self.__attached_object_ids}"
        )

    def test_lbs_block_detach_object_id(self):
        wrong_oid = 57
        with self.assertRaises(TypeError) as err:
            self.block.detach_object_id(o_id=57)
        self.assertEqual(str(err.exception), f"object id {wrong_oid} is not attached to block {self.block.get_id()}")

if __name__ == "__main__":
    unittest.main()
