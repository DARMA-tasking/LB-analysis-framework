import json
import os
import unittest

import brotli

from src.lbaf.Utils.lbsJSONDataFilesValidatorLoader import JSONDataFilesValidatorLoader

JSONDataFilesValidatorLoader().run(overwrite=True)
from src.lbaf.imported.JSON_data_files_validator import SchemaValidator  # pylint:disable=C0413:wrong-import-position

def decompress_json(input_file):
    with open(input_file, "rb") as compr_json_file:
        compr_bytes = compr_json_file.read()

    try:
        decompr_bytes = brotli.decompress(compr_bytes)
        json_data = json.loads(decompr_bytes.decode("utf-8"))

    except brotli.error:
        try:
            json_data = json.loads(compr_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            assert 0, f"Could not decompress {input_file}"

    return json_data


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.test_dir, "data", "schema")

    def test_schema_validator_valid_001(self):
        schema_file = os.path.join(self.data_dir, "valid_schema_001.json")
        vjs_json = decompress_json(schema_file)
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
        schema_file = os.path.join(self.data_dir, "invalid_schema_001.json")
        vjs_json = decompress_json(schema_file)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)

    def test_schema_validator_invalid_002(self):
        schema_file = os.path.join(self.data_dir, "invalid_schema_002.json")
        vjs_json = decompress_json(schema_file)
        is_valid = SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)


if __name__ == "__main__":
    unittest.main()
