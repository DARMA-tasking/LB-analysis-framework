#
#@HEADER
###############################################################################
#
#                          test_vt_data_extractor.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
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

import json
import io
import shutil
import unittest
import re
from contextlib import redirect_stderr, redirect_stdout
import sys


import brotli

from src.lbaf.Utils.lbsVTDataExtractor import VTDataExtractor
from src.lbaf.Utils.lbsLogging import get_logger


class TestVTDataExtractor(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.test_dir, "data", "VTDataExtractor")
        self.compr_data_dir = os.path.join(self.data_dir, "compressed_data_to_extract")
        self.uncompr_data_dir = os.path.join(self.data_dir, "uncompressed_data_to_extract")
        self.output_data_dir = os.path.join(os.path.join(os.path.dirname(__file__), "output"))
        self.expected_data_dir = os.path.join(self.data_dir, "expected")
        self.logger = get_logger()

    def tearDown(self):
        if os.path.isdir(self.output_data_dir):
            shutil.rmtree(self.output_data_dir)

    def test_vt_data_extractor_001(self):
        phases = [0, 1]
        dir_name = "test_vt_data_extractor_001"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_002(self):
        phases = [0, 1]
        dir_name = "test_vt_data_extractor_002"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.uncompr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_003(self):
        phases = ["3-4"]
        dir_name = "test_vt_data_extractor_003"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_004(self):
        phases = ["3-4"]
        dir_name = "test_vt_data_extractor_004"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.uncompr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_005(self):
        phases = [5, "6-7"]
        dir_name = "test_vt_data_extractor_005"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=True, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rb") as compr_output_file:
                output_file_bytes = compr_output_file.read()
                decompr_output_file_bytes = brotli.decompress(output_file_bytes)
                output_file_json = json.loads(decompr_output_file_bytes)
            with open(os.path.join(expected_data_dir, file), "rb") as compr_expected_file:
                expected_file_bytes = compr_expected_file.read()
                decompr_expected_file_bytes = brotli.decompress(expected_file_bytes)
                expected_file_json = json.loads(decompr_expected_file_bytes)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_006(self):
        phases = [5, "6-7"]
        dir_name = "test_vt_data_extractor_006"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.uncompr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=True, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rb") as compr_output_file:
                output_file_bytes = compr_output_file.read()
                decompr_output_file_bytes = brotli.decompress(output_file_bytes)
                output_file_json = json.loads(decompr_output_file_bytes)
            with open(os.path.join(expected_data_dir, file), "rb") as compr_expected_file:
                expected_file_bytes = compr_expected_file.read()
                decompr_expected_file_bytes = brotli.decompress(expected_file_bytes)
                expected_file_json = json.loads(decompr_expected_file_bytes)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_007(self):
        phases = [8, 9]
        dir_name = "test_vt_data_extractor_007"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=True).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_008(self):
        phases = [8, 9]
        dir_name = "test_vt_data_extractor_008"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.uncompr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=True).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_009(self):
        phases = [9]
        dir_name = "test_vt_data_extractor_009"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=True, schema_type="LBDatafile",
                        check_schema=True).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rb") as compr_output_file:
                output_file_bytes = compr_output_file.read()
                decompr_output_file_bytes = brotli.decompress(output_file_bytes)
                output_file_json = json.loads(decompr_output_file_bytes)
            with open(os.path.join(expected_data_dir, file), "rb") as compr_expected_file:
                expected_file_bytes = compr_expected_file.read()
                decompr_expected_file_bytes = brotli.decompress(expected_file_bytes)
                expected_file_json = json.loads(decompr_expected_file_bytes)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_010(self):
        phases = [9]
        dir_name = "test_vt_data_extractor_010"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.uncompr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=True, schema_type="LBDatafile",
                        check_schema=True).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rb") as compr_output_file:
                output_file_bytes = compr_output_file.read()
                decompr_output_file_bytes = brotli.decompress(output_file_bytes)
                output_file_json = json.loads(decompr_output_file_bytes)
            with open(os.path.join(expected_data_dir, file), "rb") as compr_expected_file:
                expected_file_bytes = compr_expected_file.read()
                decompr_expected_file_bytes = brotli.decompress(expected_file_bytes)
                expected_file_json = json.loads(decompr_expected_file_bytes)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_011(self):
        phases = [111, 112]
        dir_name = "test_vt_data_extractor_011"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_012(self):
        phases = ["6-5"]
        dir_name = "test_vt_data_extractor_012"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        # Check that SystemExit is raised
        with self.assertLogs(self.logger, level="ERROR") as cm:
            with self.assertRaises(SystemExit):
                VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir,
                                phases_to_extract=phases,
                                file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                                check_schema=False, logger=self.logger).main()
            # Check logger message
            self.assertEqual(cm.output, [
                "ERROR:root:Phase range wrongly declared."])

    def test_vt_data_extractor_013(self):
        phases = [2, 3]
        dir_name = "test_vt_data_extractor_013"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        input_dir = os.path.join(self.data_dir, "empty_input_dir")
        # Check that SystemExit is raised
        with self.assertLogs(self.logger, level="ERROR") as cm:
            with self.assertRaises(SystemExit):
                VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                                file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                                check_schema=False, logger=self.logger).main()
            # Check logger message
            self.assertEqual(cm.output, [
                "ERROR:root:No files were found"])

    def test_vt_data_extractor_014(self):
        phases = [2, 3]
        dir_name = "test_vt_data_extractor_014"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        input_dir = os.path.join(self.data_dir, "wrong_input_files")
        # Check that SystemExit is raised
        with self.assertLogs(self.logger, level="ERROR") as cm:
            with self.assertRaises(SystemExit):
                VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                                file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                                check_schema=False, logger=self.logger).main()
            # Check logger message
            # 2 files have wrong names but since it is loaded parallel we can expect an error for one or the other file
            invalid_values = ['sm', 'other']
            self.assertTrue(
                any(cm.output == [
                    "ERROR:root:Values in filenames can not be converted to `int`.\nPhases are not sorted.\n"
                    f"ERROR: invalid literal for int() with base 10: '{x}'"]
                    for x in invalid_values)
            )

    def test_vt_data_extractor_015(self):
        phases = [0, 1]
        dir_name = "test_vt_data_extractor_015"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        input_dir = os.path.join(self.data_dir, "uncompressed_data_to_extract")
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_016(self):
        phases = [0, 1]
        dir_name = "test_vt_data_extractor_016"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        input_dir = os.path.join(self.data_dir, "compressed_data_to_extract")
        expected_data_dir = os.path.join(self.expected_data_dir, dir_name)
        VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                        file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                        check_schema=False).main()
        for file in os.listdir(output_data_dir):
            with open(os.path.join(output_data_dir, file), "rt", encoding="utf-8") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt", encoding="utf-8") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)

    def test_vt_data_extractor_017(self):
        phases = [2, 3]
        dir_name = "test_vt_data_extractor_017"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        input_dir = "input_dir_does_not_exists"
        # Check that SystemExit is raised
        with self.assertLogs(self.logger, level="ERROR") as cm:
            with self.assertRaises(SystemExit):
                VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                                file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                                check_schema=False, logger=self.logger).main()
            # Check logger message
            self.assertEqual(cm.output, ["ERROR:root:Input data directory not found."])


if __name__ == "__main__":
    unittest.main()
