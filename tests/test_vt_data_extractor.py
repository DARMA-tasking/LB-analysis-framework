import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

import json
import shutil
import unittest

import brotli

from src.lbaf.Utils.vt_data_extractor import VTDataExtractor


class TestVTDataExtractor(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]),
                                         'data', 'VTDataExtractor')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            raise SystemExit(1)
        self.compr_data_dir = os.path.join(self.data_dir, 'compressed_data_to_extract')
        self.uncompr_data_dir = os.path.join(self.data_dir, 'uncompressed_data_to_extract')
        self.output_data_dir = os.path.join(self.data_dir, "output")
        self.expected_data_dir = os.path.join(self.data_dir, "expected")

    def tearDown(self):
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
            with open(os.path.join(output_data_dir, file), "rt") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt") as expected_file:
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
            with open(os.path.join(output_data_dir, file), "rt") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt") as expected_file:
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
            with open(os.path.join(output_data_dir, file), "rt") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt") as expected_file:
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
            with open(os.path.join(output_data_dir, file), "rt") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt") as expected_file:
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
            with open(os.path.join(output_data_dir, file), "rt") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt") as expected_file:
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
            with open(os.path.join(output_data_dir, file), "rt") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt") as expected_file:
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
            with open(os.path.join(output_data_dir, file), "rt") as output_file:
                output_file_str = output_file.read()
                output_file_json = json.loads(output_file_str)
            with open(os.path.join(expected_data_dir, file), "rt") as expected_file:
                expected_file_str = expected_file.read()
                expected_file_json = json.loads(expected_file_str)
            self.assertEqual(output_file_json, expected_file_json)


if __name__ == '__main__':
    unittest.main()
