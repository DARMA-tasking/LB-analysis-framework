import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

import json
import unittest

import brotli

from utils.schema_validator_helper import check_and_get_schema_validator
check_and_get_schema_validator()

from src.lbaf.imported.JSON_data_files_validator import SchemaValidator


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(
                f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data', 'schema')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            raise SystemExit(1)

    def test_schema_validator_valid_001(self):
        with open(os.path.join(self.data_dir, 'valid_schema_001.json'), 'rb') as compr_json_file:
            compr_bytes = compr_json_file.read()
        decompr_bytes = brotli.decompress(compr_bytes)
        vjs_json = json.loads(decompr_bytes.decode("utf-8"))
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        validated_schema = SchemaValidator(schema_type="LBDatafile").validate(schema_to_validate=vjs_json)
        self.assertEqual(vjs_json, validated_schema)
        self.assertEqual(True, is_valid)

    def test_schema_validator_valid_uncompressed_001(self):
        with open(os.path.join(self.data_dir, 'valid_schema_uncompressed_001.json'), 'r') as uncompr_json_file:
            uncompr_txt = uncompr_json_file.read()
        vjs_json = json.loads(uncompr_txt)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        validated_schema = SchemaValidator(schema_type="LBDatafile").validate(schema_to_validate=vjs_json)
        self.assertEqual(vjs_json, validated_schema)
        self.assertEqual(True, is_valid)

    def test_schema_validator_invalid_001(self):
        with open(os.path.join(self.data_dir, 'invalid_schema_001.json'), 'r') as invalid_json_schema:
            vjs_str = invalid_json_schema.read()
            vjs_json = json.loads(vjs_str)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)

    def test_schema_validator_invalid_002(self):
        with open(os.path.join(self.data_dir, 'invalid_schema_002.json'), 'r') as invalid_json_schema:
            vjs_str = invalid_json_schema.read()
            vjs_json = json.loads(vjs_str)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)


if __name__ == '__main__':
    unittest.main()
