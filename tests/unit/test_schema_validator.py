import os
import json
import unittest

import brotli

from lbaf.Applications.lbsDataFilesValidatorLoaderApplication import DataFilesValidatorLoaderApplication
loader = DataFilesValidatorLoaderApplication(interactive=False)
loader.run()

from lbaf.imported.JSON_data_files_validator import SchemaValidator


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data", "schema")

    def test_schema_validator_valid_001(self):
        with open(os.path.join(self.data_dir, "valid_schema_001.json"), "rb") as compr_json_file:
            compr_bytes = compr_json_file.read()
        decompr_bytes = brotli.decompress(compr_bytes)
        vjs_json = json.loads(decompr_bytes.decode("utf-8"))
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        validated_schema = SchemaValidator(schema_type="LBDatafile").validate(schema_to_validate=vjs_json)
        self.assertEqual(vjs_json, validated_schema)
        self.assertEqual(True, is_valid)

    def test_schema_validator_valid_uncompressed_001(self):
        with open(os.path.join(self.data_dir, "valid_schema_uncompressed_001.json"), 'r', encoding="utf-8") as uncompr_json_file:
            uncompr_txt = uncompr_json_file.read()
        vjs_json = json.loads(uncompr_txt)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        validated_schema = SchemaValidator(schema_type="LBDatafile").validate(schema_to_validate=vjs_json)
        self.assertEqual(vjs_json, validated_schema)
        self.assertEqual(True, is_valid)

    def test_schema_validator_invalid_001(self):
        with open(os.path.join(self.data_dir, "invalid_schema_001.json"), 'r', encoding="utf-8") as invalid_json_schema:
            vjs_str = invalid_json_schema.read()
            vjs_json = json.loads(vjs_str)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)

    def test_schema_validator_invalid_002(self):
        with open(os.path.join(self.data_dir, "invalid_schema_002.json"), 'r', encoding="utf-8") as invalid_json_schema:
            vjs_str = invalid_json_schema.read()
            vjs_json = json.loads(vjs_str)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)


if __name__ == "__main__":
    unittest.main()
