import os
import unittest

from src.lbaf.Applications.LBAF_app import LBAFApplication

class TestSyntheticBlocksLB(unittest.TestCase):
    """Class to run acceptance tests"""

    def setUp(self):
        return

    def tearDown(self):
        return

    def generate_configuration(self, beta: float, gamma: float, alpha0: bool):
        """Creates and returns the path to a YAML configuration file."""
        # Determine file paths
        acceptance_dir = os.path.dirname(__file__)
        test_dir = os.path.dirname(acceptance_dir)
        data_dir = os.path.join(os.path.dirname(test_dir), "data")

        # Determine data stem
        data_stem = f"{data_dir}/synthetic-blocks/synthetic-dataset-blocks"
        if alpha0:
            data_stem += "-alpha0"

        # Create YAML configuration
        config = {
            "from_data": {
                "data_stem": data_stem,
                "phase_ids": [0],
                "ranks_per_node": 2
            },
            "work_model": {
                "name": "AffineCombination",
                "parameters": {
                    "beta": beta,
                    "gamma": gamma,
                    "upper_bounds": {
                        "max_memory_usage": 36.0 if beta == 0.0 else 54.0
                    }
                }
            },
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

        # Return the configuration
        return config

    def run_test(self, config, test_case, expected_w_max):
        """Compare LBAF's results to the expected imbalance."""
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
            self.assertLessEqual(w_max, expected_w_max, f"@@@@@ [{test_case}] FOUND W_MAX: {w_max} @@@@@")

        # Clean up
        os.remove(w_max_filepath)
        os.remove(imbalance_filepath)

    def test_synthetic_blocks_lb(self):
        # Initialize test cases
        test_cases = {
            "load_only": {
                "beta": 0.0,
                "gamma": 0.0,
                "W_max": 2.5 # optimum is 2.0, but accept <= 2.5
            },
            "off_node_communication_only": {
                "beta": 1.0,
                "gamma": 0.0,
                "W_max": 0.0
            },
            "load+off_node_communication": {
                "beta": 1.0,
                "gamma": 0.0,
                "W_max": 4.5 # optimum is 4.0, but accept <= 4.5
            }
        }

        for test_case, test_params in test_cases.items():
            cfg = self.generate_configuration(
                beta=test_params["beta"],
                gamma=test_params["gamma"],
                alpha0=(test_case == "off_node_communication_only"))
            self.run_test(cfg, test_case, test_params["W_max"])


if __name__ == "__main__":
    unittest.main()
