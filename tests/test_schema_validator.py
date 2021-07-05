import json
import os
import sys
import unittest


from src.IO.schemaValidator import SchemaValidator


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            exit(1)

    def test_schema_validator_valid_001(self):
        with open(os.path.join(self.data_dir, 'valid_schema.json'), 'r') as valid_json_schema:
            vjs_str = valid_json_schema.read()
            vjs_json = json.loads(vjs_str)
        is_valid = SchemaValidator().is_valid(schema_to_validate=vjs_json)
        self.assertEqual(True, is_valid)

    def test_schema_validator_invalid_001(self):
        with open(os.path.join(self.data_dir, 'invalid_schema_001.json'), 'r') as invalid_json_schema:
            vjs_str = invalid_json_schema.read()
            vjs_json = json.loads(vjs_str)
        is_valid = SchemaValidator().is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)

    def test_schema_validator_invalid_002(self):
        with open(os.path.join(self.data_dir, 'invalid_schema_002.json'), 'r') as invalid_json_schema:
            vjs_str = invalid_json_schema.read()
            vjs_json = json.loads(vjs_str)
        is_valid = SchemaValidator().is_valid(schema_to_validate=vjs_json)
        self.assertEqual(False, is_valid)


if __name__ == '__main__':
    unittest.main()
