import os
import subprocess
import sys
import unittest


class TestStepper(unittest.TestCase):
    """Class to run acceptance tests"""

    def setUp(self):
        return

    def tearDown(self):
        return

    def test_stepper(self):
        """Runs stepper tests"""
        # run LBAF
        config_file = os.path.join(os.path.dirname(__file__), "config", "stepper.yaml")
        subprocess.run(['lbaf', '-c', config_file], check=True, stdout=sys.stdout, stderr=sys.stdout)
        log_file = os.path.join(os.path.dirname(__file__), "output", "log.txt")

        # check log file exists
        self.assertTrue(os.path.isfile(log_file), f"File: {log_file} does not exist!")

        # validate log file content
        with open(log_file, 'r', encoding="utf-8") as logger_output:
            output_str = logger_output.read()
            regex_list = [
                "cardinality: 32 sum: 10.5817 imbalance: 0.992173",
                "cardinality: 32 sum: 0.642948 imbalance: 4.91849",
                "cardinality: 32 sum: 0.526383 imbalance: 0.221116",
                "cardinality: 32 sum: 0.521197 imbalance: 0.0442304",
                "cardinality: 32 sum: 0.52225 imbalance: 0.0461051",
                "cardinality: 32 sum: 0.520378 imbalance: 0.0469951",
                "cardinality: 32 sum: 0.520078 imbalance: 0.0430356",
                "cardinality: 32 sum: 0.520286 imbalance: 0.0532831",
                "cardinality: 32 sum: 0.520617 imbalance: 0.0466161",
                "cardinality: 32 sum: 0.547612 imbalance: 1.44446",
                "cardinality: 32 sum: 0.522944 imbalance: 0.098434",
            ]
            for reg in regex_list:
                if reg in output_str:
                    print(f"Found {reg}")
                else:
                    self.fail(f"Regex: {reg} not found in log.\nTEST FAILED.")

if __name__ == "__main__":
    unittest.main()
