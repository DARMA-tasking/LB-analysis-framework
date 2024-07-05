import os
import unittest
from unittest.mock import patch
import argparse
from typing import Callable


from src.lbaf.Utils.lbsJSONDataFilesMaker import JSONDataFilesMaker

class TestJsonDataFilesMaker(unittest.TestCase):

    test_dir: str = os.path.dirname(os.path.dirname(__file__))
    config_dir: str = os.path.join(test_dir, "config", "phases")
    output_dir: str = os.path.join(test_dir, "output", "JSON_data_files_maker")

    argparse_args: Callable[..., argparse.Namespace] = lambda **kwargs: argparse.Namespace(
        spec_file=kwargs.get("spec_file"),
        data_stem=kwargs.get("data_stem"),
        interactive=kwargs.get("interactive", False),
        multiple_sharing=kwargs.get("multiple_sharing", False),
        output_config_file=kwargs.get("output_config_file", None),
        compressed=False
    )

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_01_wrong.yaml"),
        data_stem=os.path.join(output_dir, "dataset01")
    ))
    def test_make_data_files_from_spec_wrong_01(self, _namespace: argparse.Namespace):
        """Test that invalid phase configuration 01 generates no dataset and fire error"""

        with self.assertRaises(SystemExit) as err:
            JSONDataFilesMaker().run()
        self.assertEqual(err.exception.__context__.args[0],
            "Cannot assign task 1 to rank 1. It is already assigned to rank 0")

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_02_wrong.yaml"),
        data_stem=os.path.join(output_dir, "dataset02")
    ))
    def test_make_data_files_from_spec_wrong_02(self, _namespace: argparse.Namespace):
        """Test that invalid phase configuration 02 generates no dataset and fire error"""

        with self.assertRaises(SystemExit) as err:
            JSONDataFilesMaker().run()
        self.assertEqual(err.exception.__context__.args[0],
            "Task 0 already shared block 0 and cannot share additional block 2. Only 0 or 1 allowed"
        )

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_03_valid.yaml"),
        data_stem=os.path.join(output_dir, "dataset03")
    ))
    def test_make_data_files_from_spec_valid_03(self, namespace: argparse.Namespace):
        """Test that valid phase configuration correctly generates a dataset"""

        print(namespace)
        JSONDataFilesMaker().run()

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_04_valid.yaml"),
        data_stem=os.path.join(output_dir, "dataset04")
    ))
    def test_make_data_files_from_spec_valid_04(self, namespace: argparse.Namespace):
        """Test that valid phase configuration with tasks from different ranks shared same block correctly generates a dataset"""

        print(namespace)
        JSONDataFilesMaker().run()

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_05_valid.yaml"),
        data_stem=os.path.join(output_dir, "dataset05")
    ))
    def test_make_data_files_from_spec_valid_05(self, namespace: argparse.Namespace):
        """Test that valid phase configuration using dict and not lists correctly generates a dataset"""

        print(namespace)
        JSONDataFilesMaker().run()
        

if __name__ == "__main__":
    unittest.main()
