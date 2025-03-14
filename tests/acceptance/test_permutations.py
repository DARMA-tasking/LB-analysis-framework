import os
import unittest

from src.lbaf.Applications.LBAF_app import LBAFApplication

class TestPermutations(unittest.TestCase):
    """Class to run acceptance tests"""

    def setUp(self):
        return

    def tearDown(self):
        return

    def generate_configuration(self, beta, gamma, permutation):
        """Creates and returns the path to a YAML configuration file."""
        # Determine filepaths
        acceptance_dir = os.path.dirname(__file__)
        test_dir = os.path.dirname(acceptance_dir)
        data_dir = os.path.join(os.path.dirname(test_dir), "data")

        # Create YAML configuration
        config = {
            "from_data": {
                "data_stem": f"{data_dir}/synthetic_lb_data/data",
                "phase_ids": [0],
            },
            "check_schema": False,
            "work_model": {
                "name": "AffineCombination",
                "parameters": {
                    "beta": beta,
                    "gamma": gamma
                }
            },
            "algorithm": {
                "name": "PrescribedPermutation",
                "phase_id": 0,
                "parameters": {
                    "permutation": permutation
                }
            },
            "logging_level": "info",
            "output_dir": os.path.join(acceptance_dir, "output"),
            "output_file_stem": "output_file"
        }

        # Return the configuration
        return config

    def run_test(self, config, test_case, expected_w_max):
        """Compare LBAF's results to the expected W_max."""
        # Determine current directory
        acceptance_dir = os.path.dirname(__file__)

        # Run LBAF
        lbaf = LBAFApplication()
        lbaf.run(cfg=config, cfg_dir=acceptance_dir)

        # Check w_max file exists
        output_dir = os.path.join(acceptance_dir, "output")
        imbalance_filepath = os.path.join(output_dir, "imbalance.txt")
        w_max_filepath = os.path.join(output_dir, "w_max.txt")
        self.assertTrue(os.path.isfile(w_max_filepath), f"File: {w_max_filepath} does not exist!")

        # Validate w_max value
        with open(w_max_filepath, 'r', encoding="utf-8") as w_max_file:
            w_max = float(w_max_file.read())
            self.assertEqual(w_max, expected_w_max, f"@@@@@ [{test_case}] FOUND W_MAX: {w_max} @@@@@")

        # Clean up
        os.remove(w_max_filepath)
        os.remove(imbalance_filepath)

    def test_ccm_permutation(self):
        # Initialize test cases
        test_cases = {
            "load_only": {
                "beta": 0.0,
                "gamma": 0.0,
                "permutation": dict(enumerate([0, 0, 1, 1, 0, 2, 1, 3, 3])),
                "W_max": 2.0
            },
            "off_node_communication_only": {
                "beta": 1.0,
                "gamma": 0.0,
                "permutation": dict(enumerate([3, 2, 3, 3, 2, 3, 3, 3, 3])),
                "W_max": 0.0
            }
        }

        # Run each test case
        for test_case, test_params in test_cases.items():
            cfg = self.generate_configuration(
                beta=test_params["beta"],
                gamma=test_params["gamma"],
                permutation=test_params["permutation"]
            )
            self.run_test(cfg, test_case, test_params["W_max"])


if __name__ == "__main__":
    unittest.main()
