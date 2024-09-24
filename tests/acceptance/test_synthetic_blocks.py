import os
import sys
import subprocess
import unittest
import tempfile
import yaml

class TestSyntheticBlocksLB(unittest.TestCase):
    """Class to run acceptance tests"""

    def setUp(self):
        return

    def tearDown(self):
        return

    def generate_configuration_file(self, alpha, beta, gamma):
        """Creates and returns the path to a YAML configuration file."""
        acceptance_dir = os.path.dirname(__file__)
        test_dir = os.path.dirname(acceptance_dir)
        data_dir = os.path.join(os.path.dirname(test_dir), "data")
        config = {
            "from_data": {
                "data_stem": f"{data_dir}/synthetic-blocks/synthetic-dataset-blocks",
                "phase_ids": [0]
            },
            "work_model": {
                "name": "AffineCombination",
                "parameters": {
                    "alpha": alpha,
                    "beta": beta,
                    "gamma": gamma
                }
            },
            "brute_force_optimization": False,
            "algorithm": {
                "name": "InformAndTransfer",
                "phase_id": 0,
                "parameters": {
                    "n_iterations": 10,
                    "n_rounds": 2,
                    "fanout": 2,
                    "order_strategy": "element_id",
                    "transfer_strategy": "Recursive",
                    "criterion": "Tempered",
                    "max_objects_per_transfer": 8,
                    "deterministic_transfer": True
                }
            },
            "logging_level": "info",
            "output_dir": os.path.join(acceptance_dir, "output"),
            "output_file_stem": "output_file"
        }

        # Write out the configuration to a temporary file
        tmp_cfg_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w")
        with tmp_cfg_file as f:
            yaml.dump(config, f)

        # Return the path to the config file
        return tmp_cfg_file.name

    def run_lb_test(self, config_file, expected_w_max, test_case):
        """Compare LBAF's results to the expected imbalance."""
        # run LBAF
        subprocess.run(["python", "src/lbaf", "-c", config_file], check=True)

        w_max_filepath = os.path.join(os.path.dirname(__file__), "output", "w_max.txt")

        # check w_max file exists
        self.assertTrue(os.path.isfile(w_max_filepath), f"File: {w_max_filepath} does not exist!")

        # validate imbalance value
        with open(w_max_filepath, 'r', encoding="utf-8") as w_max_file:
            w_max = float(w_max_file.read())
            self.assertEqual(w_max, expected_w_max, f"@@@@@ [{test_case}] FOUND W_MAX: {w_max} @@@@@")

        # Delete the config and imbalance files
        os.remove(config_file)
        os.remove(w_max_filepath)

    def test_synthetic_blocks_lb(self):
        # Initialize test cases
        test_cases = {
            "load_only": {
                "alpha": 1.0,
                "beta": 0.0,
                "gamma": 0.0,
                "W_max": 2.0
            },
            "off_node_communication_only": {
                "alpha": 0.0,
                "beta": 1.0,
                "gamma": 0.0,
                "W_max": 0.0
            },
            "load+off_node_communication": {
                "alpha": 1.0,
                "beta": 1.0,
                "gamma": 0.0,
                "W_max": 4.0
            }
        }

        for test_case, test_params in test_cases.items():
            cfg = self.generate_configuration_file(
                alpha=test_params["alpha"],
                beta=test_params["beta"],
                gamma=test_params["gamma"]
            )
            self.run_lb_test(cfg, test_params["W_max"], test_case)


if __name__ == "__main__":
    unittest.main()
