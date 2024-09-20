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
            "brute_force_optimization": True,
            "algorithm": {
                "name": "InformAndTransfer",
                "phase_id": 0,
                "parameters": {
                    "n_iterations": 8,
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

    def run_lb_test(self, config_file, expected_imb):
        """Compare LBAF's results to the expected imbalance."""
        # run LBAF
        subprocess.run(["python", "src/lbaf", "-c", config_file], check=True)

        imbalance_file = os.path.join(os.path.dirname(__file__), "output", "imbalance.txt")

        # check imbalance file exists
        self.assertTrue(os.path.isfile(imbalance_file), f"File: {imbalance_file} does not exist!")

        # validate imbalance value
        with open(imbalance_file, 'r', encoding="utf-8") as imb_file:
            imb_level = float(imb_file.read())
            self.assertEqual(imb_level, expected_imb, f"@@@@@ FOUND IMBALANCE: {imb_level} @@@@@")

        # Delete the config and imbalance files
        os.remove(config_file)
        os.remove(imbalance_file)

    def test_synthetic_blocks_lb(self):
        combinations = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]
        exp_imbalances = [0.00, 0.00, 0.25]
        self.assertEqual(len(combinations), len(exp_imbalances))
        for i in range(len(combinations)):
            params = combinations[i]
            cfg = self.generate_configuration_file(
                alpha=params[0],
                beta=params[1],
                gamma=params[2]
            )
            self.run_lb_test(cfg, exp_imbalances[i])


if __name__ == "__main__":
    unittest.main()
