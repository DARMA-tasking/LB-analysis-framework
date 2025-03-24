import os
import sys
import subprocess
import unittest


class TestSyntheticBlocks(unittest.TestCase):
    """Class to run synthetic block acceptance tests"""

    def setUp(self):
        return

    def tearDown(self):
        return

    def test_synthetic_blocks(self):
        """Runs acceptance tests"""
        # run LBAF
        config_file = os.path.join(os.path.dirname(__file__), "config", "synthetic-blocks.yaml")
        subprocess.run(["python", "src/lbaf", "-c", config_file], check=True)

        imbalance_file = os.path.join(os.path.dirname(__file__), "output", "imbalance.txt")

        # check imbalance file exists
        self.assertTrue(os.path.isfile(imbalance_file), f"File: {imbalance_file} does not exist!")

        # validate imbalance value
        with open(imbalance_file, 'r', encoding="utf-8") as imb_file:
            imb_level = float(imb_file.read())
            self.assertLess(imb_level, 0.000001, f"@@@@@ FOUND IMBALANCE: {imb_level} @@@@@")

if __name__ == "__main__":
    unittest.main()
