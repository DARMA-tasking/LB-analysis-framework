import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    exit(1)

import argparse
import logging
import unittest
from unittest.mock import Mock

from schema import SchemaError

from src.lbaf.Utils.JSON_data_files_validator import JSONDataFilesValidator


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            exit(1)
        self.file_path = os.path.join(self.data_dir, 'JSON_data_file_validator', 'data.0.json')
        self.wrong_file_path = os.path.join(self.data_dir, 'JSON_data_file_validator', 'data.0.jso')
        self.wrong_file_schema = os.path.join(self.data_dir, 'JSON_data_file_validator_wrong', 'data.0.json')
        self.dir_path = os.path.join(self.data_dir, 'JSON_data_file_validator')
        self.dir_path_compressed = os.path.join(self.data_dir, 'JSON_data_file_validator_compressed')
        self.dir_path_empty = os.path.join(self.data_dir, 'JSON_data_file_validator_empty')
        self.wrong_dir_path = os.path.join(self.data_dir, 'wrong_dir_path')
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

    def test_json_data_files_validator_prefix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix='data',
                                                                             file_suffix=None)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_suffix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix='json')
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_prefix_suffix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix='data',
                                                                             file_suffix='json')
        JSONDataFilesValidator().main()

    # Seems CI is not copying empty dir
    # def test_json_data_files_validator_empty(self):
    #     argparse.ArgumentParser.parse_args = Mock()
    #     argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
    #                                                                          dir_path=self.dir_path_empty,
    #                                                                          file_prefix=None,
    #                                                                          file_suffix=None)
    #     with self.assertRaises(FileNotFoundError) as err:
    #         JSONDataFilesValidator().main()
    #     self.assertEqual(err.exception.args[0], f"Directory: {self.dir_path_empty} is EMPTY!")

    def test_json_data_files_validator_file_not_found(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.wrong_file_path,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(FileNotFoundError) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], f"File: {self.wrong_file_path} NOT found!")

    def test_json_data_files_validator_dir_not_found(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.wrong_dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(FileNotFoundError) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], f"Directory: {self.wrong_dir_path} does NOT exist!")

    def test_json_data_files_validator_no_args(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(Exception) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], "FILE path or DIRECTORY path has to be given!")

    def test_json_data_files_validator_wrong_file_schema(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.wrong_file_schema,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None)
        with self.assertRaises(SchemaError) as err:
            JSONDataFilesValidator().main()
        with open(os.path.join(self.data_dir, 'JSON_data_file_validator_wrong', 'schema_error.txt'), 'rt') as se:
            err_msg = se.read()
        self.assertEqual(err.exception.args[0], err_msg)


if __name__ == '__main__':
    unittest.main()
