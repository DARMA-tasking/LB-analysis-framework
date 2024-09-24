#
#@HEADER
###############################################################################
#
#                           test_schema_validator.py
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
