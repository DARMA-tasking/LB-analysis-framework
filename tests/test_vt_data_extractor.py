import os
import sys

import json
import shutil
import unittest

import brotli

from lbaf.Utils.common import project_dir
from lbaf.Utils.vt_data_extractor import VTDataExtractor


class TestVTDataExtractor(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(project_dir(), "tests", "data", "VTDataExtractor")
        self.compr_data_dir = os.path.join(self.data_dir, "compressed_data_to_extract")
        self.uncompr_data_dir = os.path.join(self.data_dir, "uncompressed_data_to_extract")
        self.output_data_dir = os.path.join(project_dir(), "tests", "output")
        self.expected_data_dir = os.path.join(self.data_dir, "expected")

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
        with self.assertRaises(SystemExit) as err:
            VTDataExtractor(input_data_dir=self.compr_data_dir, output_data_dir=output_data_dir,
                            phases_to_extract=phases,
                            file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                            check_schema=False).main()
        self.assertEqual(err.exception.args[0], "Phase range wrongly declared.")

    def test_vt_data_extractor_013(self):
        phases = [2, 3]
        dir_name = "test_vt_data_extractor_013"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        input_dir = os.path.join(self.data_dir, "empty_input_dir")
        with self.assertRaises(SystemExit) as err:
            VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                            file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                            check_schema=False).main()
        self.assertEqual(err.exception.args[0], "No files were found")

    def test_vt_data_extractor_014(self):
        phases = [2, 3]
        dir_name = "test_vt_data_extractor_014"
        output_data_dir = os.path.join(self.output_data_dir, dir_name)
        input_dir = os.path.join(self.data_dir, "wrong_input_files")
        with self.assertRaises(ValueError) as err:
            VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                            file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                            check_schema=False).main()
        expected = ["Values in filenames can not be converted to `int`.\nPhases are not sorted.\nERROR: invalid litera"
                    "l for int() with base 10: 'other'",
                    "Values in filenames can not be converted to `int`.\nPhases are not sorted.\nERROR: invalid litera"
                    "l for int() with base 10: 'sm'"]
        self.assertIn(err.exception.args[0], expected)

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
        with self.assertRaises(SystemExit) as err:
            VTDataExtractor(input_data_dir=input_dir, output_data_dir=output_data_dir, phases_to_extract=phases,
                            file_prefix="data", file_suffix="json", compressed=False, schema_type="LBDatafile",
                            check_schema=False).main()
        self.assertEqual(err.exception.args[0], "Input data directory not found.")


if __name__ == "__main__":
    unittest.main()
