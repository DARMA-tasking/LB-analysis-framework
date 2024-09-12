"""Tests for the VTDataWriter class"""

import json
import os
import subprocess
import unittest
from typing import Any

import brotli
import yaml
from schema import Optional, And

from src.lbaf.Utils.lbsJSONDataFilesValidatorLoader import JSONDataFilesValidatorLoader
from src.lbaf.Utils.lbsPath import abspath

JSONDataFilesValidatorLoader().run(overwrite=True)
from src.lbaf.imported.JSON_data_files_validator import SchemaValidator  # pylint:disable=C0413:wrong-import-position


class TestVTDataWriter(unittest.TestCase):
    """Test class for VTDataWriter class"""

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.config_dir = os.path.join(self.test_dir, "config")
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
        elif isinstance(nodes, dict):
            for key, item in nodes.items():
                key_as_string = key if isinstance(key, str) else key.schema
                if isinstance(key, Optional):
                    opt_nodes.append(dot_path + key_as_string)
                opt_nodes += self.__list_optional_keys_recursive(item, dot_path + key_as_string + '.')

        elif isinstance(nodes, And):
            for a in nodes.args:
                opt_nodes += self.__list_optional_keys_recursive([ a ], dot_path)

        return opt_nodes

    def __remove_optional_keys_recursive(self, data: dict, optional_keys: list, dot_path: str = ''):
        # Values that we want to test even it is optional
        do_keep_exceptions = [ "phases.tasks.entity.seq_id" ]

        to_delete = []
        for key, value in data.items():
            child_dot_path = dot_path + key
            if (child_dot_path in optional_keys and data.get(key) is not None and
                not child_dot_path in do_keep_exceptions):
                to_delete.append(key)
            elif isinstance(value, dict):
                self.__remove_optional_keys_recursive(value, optional_keys, child_dot_path + ".")
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.__remove_optional_keys_recursive(item, optional_keys, child_dot_path + ".")

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
            if isinstance(data[0], dict):
                for id_field in ["id", "seq_id"]:
                    if id_field in data[0]:
                        sorted_list = sorted(data, key=lambda item, k=id_field: item.get(k))
                        data = sorted_list
                        break
            # if list recursive sort children
            sorted_data = []
            for item in data:
                sorted_data.append(self.__sort_data_recursive(item))
            data = sorted_data
        return data

    def __sort_phases_tasks(self, data):
        """Sort phases by entity ids (required to compare input and output data files)"""

        phases = data.get("phases")
        if phases is not None:
            for phase in phases:
                tasks = phase.get("tasks")
                if tasks is not None:
                    phase["tasks"] = sorted(tasks, key=lambda item: item.get("entity").get("seq_id"))
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

        # JSON schema validator
        schema_validator = SchemaValidator(schema_type="LBDatafile")
        # > find optional nodes
        opt_keys = self.__list_optional_keys_recursive(schema_validator.valid_schema.schema)
        print("Ignoring optional keys: ")
        print(opt_keys)

        # run LBAF
        config_file = os.path.join(self.config_dir, "conf_vt_writer_stepper_test.yml")
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

            # validate that output file exists at rank i
            self.assertTrue(
                os.path.isfile(output_file),
                f"File {output_file} not generated at {output_dir}"
            )

            # read input and output files
            input_data = self.__read_data_file(input_file)
            output_data = self.__read_data_file(output_file)

            # validate output data against schema
            self.assertTrue(
                schema_validator.validate(output_data),
                f"Schema not valid for generated file at {output_file_name}"
            )

            # compare input & output data
            # > remove optional nodes from input and output data
            self.__remove_optional_keys_recursive(input_data, opt_keys)
            self.__remove_optional_keys_recursive(output_data, opt_keys)
            # > sort dictionaries and lists of elements by id
            input_data = self.__sort_data_recursive(input_data)
            output_data = self.__sort_data_recursive(output_data)
            # > sort phases tasks
            self.__sort_phases_tasks(input_data)
            self.__sort_phases_tasks(output_data)

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

    def test_vt_writer_communications_output(self):
        """Tests that LBAF writes out the correct communications data."""

        # run LBAF
        config_file = os.path.join(self.config_dir, "conf_vt_writer_communications_test.yaml")
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

        # count total communications
        input_communication_count = 0
        output_communication_count = 0

        # compare input/output files (at each rank)
        for r_id in range(0, n_ranks):
            input_file_name = f"{input_file_prefix}.{r_id}.json"
            input_file = os.path.join(input_dir, input_file_name)
            output_file_name = f"{output_file_prefix}.{r_id}.json"
            output_file = os.path.join(output_dir, output_file_name)

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

            # ensure that input and output have same number of phases
            self.assertEqual(len(input_data["phases"]), len(output_data["phases"]))

            # get current phase
            p_id = config.get("algorithm")["phase_id"]

            # Find index of current phase
            idx = 0
            for phase_dict in input_data["phases"]:
                if phase_dict["id"] == p_id:
                    break
                else:
                    idx += 1

            # Isolate phase dicts
            input_phase_dict = input_data["phases"][idx]
            output_phase_dict = output_data["phases"][idx]

            # increment the input communication counter
            if "communications" in input_phase_dict:
                input_communication_data = input_phase_dict["communications"]
                input_communication_count += len(input_communication_data)

            # increment the output communication counter
            if "communications" in output_phase_dict:
                output_communication_data = output_phase_dict["communications"]
                output_communication_count += len(output_communication_data)

                # get list of all objects on this rank
                rank_objs = []
                tasks = output_phase_dict["tasks"]
                for task in tasks:
                    rank_objs.append(task["entity"].get("id", task["entity"].get("seq_id")))

                # Make sure all communicating objects belong on this rank
                for comm_dict in output_communication_data:
                    comm_obj = comm_dict["from"].get("id", comm_dict["from"].get("seq_id"))
                    if comm_dict["from"]["migratable"]: # ignore sentinel objects
                        self.assertIn(comm_obj, rank_objs, f"Object {comm_obj} is not on rank {r_id}")

        # make sure no communications were lost
        self.assertEqual(input_communication_count, output_communication_count)

if __name__ == "__main__":
    unittest.main()
