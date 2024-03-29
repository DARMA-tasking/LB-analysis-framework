import os

import argparse
import logging
import unittest
from unittest.mock import Mock

from schema import SchemaError

from src.lbaf.Utils.lbsJSONDataFilesValidatorLoader import JSONDataFilesValidatorLoader
loader = JSONDataFilesValidatorLoader()
loader.run({ "overwrite": True })

from src.lbaf.imported.JSON_data_files_validator import JSONDataFilesValidator


class TestJSONDataFilesValidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.test_dir, "data")
        self.file_path = os.path.join(self.data_dir, "JSON_data_file_validator", "data.0.json")
        self.wrong_file_path = os.path.join(self.data_dir, "JSON_data_file_validator", "data.0.jso")
        self.wrong_file_schema = os.path.join(self.data_dir, "JSON_data_file_validator_wrong", "data.0.json")
        self.stats_file_001 = os.path.join(self.data_dir, "JSON_data_file_validator_stats", "vt_lb_statistics_001.json")
        self.stats_file_002 = os.path.join(self.data_dir, "JSON_data_file_validator_stats", "vt_lb_statistics_002.json")
        self.stats_file_003 = os.path.join(self.data_dir, "JSON_data_file_validator_stats", "vt_lb_statistics_003.json")
        self.stats_file_004 = os.path.join(self.data_dir, "JSON_data_file_validator_stats", "vt_lb_statistics_004.json")
        self.vt_lb_statistics_wrong = os.path.join(self.data_dir, "JSON_data_file_validator_stats",
                                                   "vt_lb_statistics_wrong.json")
        self.vt_lb_statistics_no_schema_type = os.path.join(self.data_dir, "JSON_data_file_validator_stats",
                                                            "vt_lb_statistics_no_schema_type.json")
        self.dir_path = os.path.join(self.data_dir, "JSON_data_file_validator")
        self.dir_path_compressed = os.path.join(self.data_dir, "JSON_data_file_validator_compressed")
        self.dir_path_empty = os.path.join(self.data_dir, "JSON_data_file_validator_empty")
        self.wrong_dir_path = os.path.join(self.data_dir, "wrong_dir_path")
        self.logger = logging.getLogger()

    def test_json_data_files_validator_file(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.file_path,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_dir(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_dir_compressed(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path_compressed,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_001(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_001,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_002(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_002,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_003(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_003,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_004(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_004,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_no_schema_type(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(
            file_path=self.vt_lb_statistics_no_schema_type, dir_path=None, file_prefix=None, file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_prefix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix="data",
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_suffix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix="json")
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_prefix_suffix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix="data",
                                                                             file_suffix="json")
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_not_found(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.wrong_file_path,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(FileNotFoundError) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], f"File: {self.wrong_file_path} NOT found")

    def test_json_data_files_validator_dir_not_found(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.wrong_dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(FileNotFoundError) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], f"Directory: {self.wrong_dir_path} does NOT exist")

    def test_json_data_files_validator_no_args(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(Exception) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], "FILE path or DIRECTORY path has to be given")

    def test_json_data_files_validator_wrong_file_schema(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.wrong_file_schema,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(SchemaError) as err:
            JSONDataFilesValidator().main()
        with open(os.path.join(self.data_dir, "JSON_data_file_validator_wrong", "schema_error.txt"), "rt") as se:
            err_msg = se.read()
        self.assertEqual(err.exception.args[0], err_msg)


if __name__ == "__main__":
    unittest.main()
