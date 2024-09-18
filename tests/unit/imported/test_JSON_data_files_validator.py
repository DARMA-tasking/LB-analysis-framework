#
#@HEADER
###############################################################################
#
#                      test_JSON_data_files_validator.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
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
        self.test_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.data_dir = os.path.join(self.test_dir, "data")
        self.file_path = os.path.join(self.data_dir, "JSON_data_file_validator", "data.0.json")
        self.comm_links_file_path = os.path.join(self.data_dir, "JSON_data_file_validator_comm_links", "data.0.json")
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
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_dir(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_dir_compressed(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path_compressed,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_001(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_001,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_002(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_002,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_003(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_003,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_004(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.stats_file_004,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_stats_no_schema_type(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(
            file_path=self.vt_lb_statistics_no_schema_type, dir_path=None, file_prefix=None, file_suffix=None,
            validate_comm_links=False,
            debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_prefix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix="data",
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_suffix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix="json",
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_prefix_suffix(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.dir_path,
                                                                             file_prefix="data",
                                                                             file_suffix="json",
                                                                             validate_comm_links=False,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_validator_file_not_found(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.wrong_file_path,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        with self.assertRaises(FileNotFoundError) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], f"File: {self.wrong_file_path} NOT found")

    def test_json_data_files_validator_dir_not_found(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=self.wrong_dir_path,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        with self.assertRaises(FileNotFoundError) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], f"Directory: {self.wrong_dir_path} does NOT exist")

    def test_json_data_files_validator_no_args(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=None,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        with self.assertRaises(Exception) as err:
            JSONDataFilesValidator().main()
        self.assertEqual(err.exception.args[0], "FILE path or DIRECTORY path has to be given")

    def test_json_data_files_validator_wrong_file_schema(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.wrong_file_schema,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=False)
        with self.assertRaises(SchemaError) as err:
            JSONDataFilesValidator().main()
        self.maxDiff = None
        self.assertRegex(err.exception.args[0], r"Key 'phases' error:\n(.*)\nMissing key: 'tasks'")

    def test_json_data_files_validate_comm_links(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.comm_links_file_path,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=True,
                                                                             debug=False)
        JSONDataFilesValidator().main()

    def test_json_data_files_debug(self):
        argparse.ArgumentParser.parse_args = Mock()
        argparse.ArgumentParser.parse_args.return_value = argparse.Namespace(file_path=self.file_path,
                                                                             dir_path=None,
                                                                             file_prefix=None,
                                                                             file_suffix=None,
                                                                             validate_comm_links=False,
                                                                             debug=True)
        JSONDataFilesValidator().main()

if __name__ == "__main__":
    unittest.main()
