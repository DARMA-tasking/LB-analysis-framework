"""Tests for the VTDataWriter class"""

import json
import os
import subprocess
import unittest
from typing import Any

import brotli
import yaml
from schema import Optional

from src.lbaf.Utils.lbsJSONDataFilesValidatorLoader import JSONDataFilesValidatorLoader
from src.lbaf.Utils.lbsPath import abspath

JSONDataFilesValidatorLoader().run(overwrite=True)
from src.lbaf.imported.JSON_data_files_validator import SchemaValidator  # pylint:disable=C0413:wrong-import-position


class TestVTDataWriter(unittest.TestCase):
    """Test class for VTDataWriter class"""

    def setUp(self):
        return

    def tearDown(self):
        return

    def __list_optional_keys_recursive(self, nodes: Any, dot_path: str = ''):
        """List optional keys as some dot path notation"""
        opt_nodes = []

        if isinstance(nodes, list):
            for item in nodes:
                opt_nodes += self.__list_optional_keys_recursive(item, dot_path)
            return opt_nodes

        # Key & node
        if isinstance(nodes, dict):
            for key, item in nodes.items():
                key_as_string = key if isinstance(key, str) else key.schema
                if isinstance(key, Optional):
                    opt_nodes.append(dot_path + key_as_string)
                else:
                    opt_nodes += self.__list_optional_keys_recursive(item, dot_path + key_as_string + '.')
        return opt_nodes

    def __remove_optional_keys_recursive(self, data: dict, optional_keys: list, dot_path: str = ''):
        to_delete = []
        for key, value in data.items():
            if dot_path + key in optional_keys and data.get(key) is not None:
                to_delete.append(key)
            elif isinstance(value, dict):
                self.__remove_optional_keys_recursive(value, optional_keys, dot_path + key + ".")
            elif isinstance(value, list):
                for item in value:
                    self.__remove_optional_keys_recursive(item, optional_keys, dot_path + key + ".")

        for k in to_delete:
            del data[k]

    def __sort_data_recursive(self, data) -> dict:
        """Sort dict by keys and also sort lists by element id if available. Recursive."""

        # sort keys
        if isinstance(data, dict):
            dict_keys = list(data.keys())
            dict_keys.sort()
            sorted_data = {i: data[i] for i in dict_keys}
            data = sorted_data
            # sort elements by id in a list of objects if id key exists
            for key, item in data.items():
                data[key] = self.__sort_data_recursive(item)
        elif isinstance(data, list):
            if isinstance(data[0], dict) and "id" in data[0]:
                sorted_list = sorted(data, key=lambda item: item.get("id"))
                data = sorted_list
            # if list recursive sort children
            sorted_data = []
            for item in data:
                sorted_data.append(self.__sort_data_recursive(item))
            data = sorted_data
        return data

    def __sort_phases_by_entity_id(self, data):
        """Sort phases by entity ids (required to compare input and output data files)"""

        phases = data.get("phases")
        if phases is not None:
            for phase in phases:
                tasks = phase.get("tasks")
                if phase.get("tasks") is not None:
                    phase["tasks"] = sorted(tasks, key=lambda item: item.get("entity").get("id"))
            data["phases"] = phases

    def __read_data_file(self, file_path):
        """Get uncompressed data file content"""

        with open(file_path, "rb") as compr_json_file:
            compr_bytes = compr_json_file.read()
            try:
                decompr_bytes = brotli.decompress(compr_bytes)
                decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))  # , object_pairs_hook=OrderedDict
            except brotli.error:
                decompressed_dict = json.loads(compr_bytes.decode("utf-8"))  # , object_pairs_hook=OrderedDict
        return decompressed_dict

    def test_vt_writer_required_fields_output(self):
        """Run LBAF using a PhaseStepper algorithm and test that output is same than input data files
        (required fields only).
        Note that the dictionary keys and list of elements can be ordered differently in the input and in the output
        data.
        """

        # run LBAF
        config_file = os.path.join(os.path.dirname(__file__), "config", "conf_vt_writer_stepper_test.yml")
        proc = subprocess.run(["python", "src/lbaf", "-c", config_file], check=True)
        self.assertEqual(0, proc.returncode)

        # LBAF config useful information
        with open(config_file, "rt", encoding="utf-8") as file_io:
            config = yaml.safe_load(file_io)
        data_stem = config.get("from_data").get("data_stem")

        # input information
        input_dir = abspath(f"{os.sep}".join(data_stem.split(os.sep)[:-1]), os.path.dirname(config_file))
        input_file_prefix = data_stem.split(os.sep)[-1]
        n_ranks = len([name for name in os.listdir(input_dir)])

        # output information
        output_dir = abspath(config.get("output_dir", '.'), os.path.dirname(config_file))
        output_file_prefix = config.get("output_file_stem")

        # compare input/output files (at each rank)
        for i in range(0, n_ranks):
            input_file_name = f"{input_file_prefix}.{i}.json"
            input_file = os.path.join(input_dir, input_file_name)
            output_file_name = f"{output_file_prefix}.{i}.json"
            output_file = os.path.join(output_dir, output_file_name)

            print(f"[{__loader__.name}] Compare input file ({input_file_name}) and output file ({output_file_name})...")

            # validate that output file exists at rank i
            self.assertTrue(
                os.path.isfile(output_file),
                f"File {output_file} not generated at {output_dir}"
            )

            # read input and output files
            input_data = self.__read_data_file(input_file)
            output_data = self.__read_data_file(output_file)

            # validate output against the JSON schema validator
            schema_validator = SchemaValidator(schema_type="LBDatafile")
            self.assertTrue(
                schema_validator.validate(output_data),
                f"Schema not valid for generated file at {output_file_name}"
            )

            # compare input & output data
            # > find optional nodes
            opt_keys = self.__list_optional_keys_recursive(schema_validator.valid_schema.schema)
            # > remove optional nodes from input and output data
            self.__remove_optional_keys_recursive(input_data, opt_keys)
            self.__remove_optional_keys_recursive(output_data, opt_keys)
            # > sort dictionaries and lists of elements by id
            input_data = self.__sort_data_recursive(input_data)
            output_data = self.__sort_data_recursive(output_data)
            # > sort phases by inner entity id
            self.__sort_phases_by_entity_id(input_data)
            self.__sort_phases_by_entity_id(output_data)

            # uncomment to see complete data file contents (uncompressed)
            # print(f"-------------------------------{input_file_name}-----------------------------------")
            # print(json.dumps(input_data, indent=4))
            # print(f"-------------------------------{output_file_name}----------------------------------")
            # print(json.dumps(output_data, indent=4))
            # print("-----------------------------------------------------------------------")

            self.maxDiff = None  # to remove diff limit if self.assertDictEqual returns large diffs
            self.assertDictEqual(input_data, output_data)

            # the following is an assert alternative to compare json encoded data instead of dictionaries
            # self.assertEqual(json.dumps(input_data, indent=4), json.dumps(output_data, indent=4))


if __name__ == "__main__":
    unittest.main()
