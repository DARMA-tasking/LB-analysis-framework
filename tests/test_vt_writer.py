"""Tests for the VT Writer"""
import json
import os
import subprocess
import sys
import unittest

import brotli
import yaml
from lbaf import PROJECT_PATH
from lbaf.Utils.path import abspath
from lbaf.Applications.JSON_data_files_validator_loader import load as load_schema
load_schema()
from lbaf.imported.JSON_data_files_validator import SchemaValidator


def mydata_hook(obj):
    obj_d = dict(obj)
    if 'Id' in obj_d:
        return {'Id': obj_d['Id'], 'mydata': {k: v for k, v in obj_d.items() if 'Id' not in k}}
    else:
        return obj_d

class TestVTDataWriter(unittest.TestCase):
    """Test class for VTDataWriter"""

    output_dir: str

    def setUp(self):
        self.output_dir = os.path.join(PROJECT_PATH, 'output', 'vt_writer_null_test')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def tearDown(self):
        # shutil.rmtree(self.output_dir)
        return

    def _run_lbaf(self, config_file) -> subprocess.CompletedProcess:
        """Run lbaf as a subprocess"""

        lbaf_path = os.path.join(PROJECT_PATH, 'src', 'lbaf', 'Applications', 'LBAF_app.py')
        proc = subprocess.run(
            [
                sys.executable,
                lbaf_path,
                '-c',
                config_file
            ],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stdout
        )
        return proc

    def __sort_data(self, data):
        phases = data.get('phases')
        if phases is not None:
            phases = sorted(phases, key=lambda item: item.get('id'))
            for phase in phases:
                tasks = phase.get('tasks')
                if phase.get("tasks") is not None:
                    tasks = sorted(tasks, key=lambda item: item.get('entity').get('id'))
                    for task in tasks:
                        entity = task['entity']
                        entity_keys = list(entity.keys())
                        entity_keys.sort()
                        task['entity'] = {i: entity[i] for i in entity_keys}
                    phase['tasks'] = tasks
            data['phases'] = phases

    def __remove_non_applicable_keys_from_input_data(self, data):
        del data['type']
        phases = data.get('phases')
        if phases is not None:
            for phase in phases:
                tasks = phase.get('tasks')
                if phase.get("tasks") is not None:
                    for task in tasks:
                        entity = task['entity']
                        del entity['index']
                        del entity['collection_id']
                        del task['user_defined']
                    phase['tasks'] = tasks
            data['phases'] = phases

    def __remove_non_applicable_keys_from_output_data(self, data):
        del data['metadata']

    def test_vt_writer_null_test_valid_output(self):
        """run LBAF with a null test"""

        config_file = os.path.join(os.path.dirname(__file__), 'config', 'conf_vt_writer_null_test.yml')
        proc = self._run_lbaf(config_file)
        self.assertEqual(0, proc.returncode)

        # check output
        with open(config_file, "rt", encoding="utf-8") as file_io:
            config = yaml.safe_load(file_io)
        data_stem = config.get('from_data').get('data_stem')
        input_dir = f"{os.sep}".join(data_stem.split(os.sep)[:-1])
        input_dir = abspath(input_dir, os.path.dirname(config_file))
        input_file_prefix = data_stem.split(os.sep)[-1]
        n_ranks = len([name for name in os.listdir(input_dir)])
        output_file_prefix = config.get('output_file_stem')
        output_dir = abspath(config.get("output_dir", '.'), os.path.dirname(config_file))

        for i in range(0, n_ranks):
            input_file_name = f"{input_file_prefix}.{i}.json"
            input_file = os.path.join(input_dir, input_file_name)
            output_file_name = f"{output_file_prefix}.{i}.json"
            output_file = os.path.join(output_dir, output_file_name)

            # validate file has been written
            self.assertTrue(
                os.path.isfile(output_file),
                f'File {output_file} not generated at {output_dir}')

            # retrieve generated content
            input_file_content = ""
            with open(input_file, "rt", encoding="utf-8") as input_file_io:
                input_file_content = input_file_io.read()
                input_dict = json.loads(input_file_content) # , object_pairs_hook=OrderedDict
            with open(output_file, "rb") as output_file_io:
                compr_bytes = output_file_io.read()
                try:
                    output_file_content = brotli.decompress(compr_bytes)
                    output_dict = json.loads(output_file_content.decode("utf-8")) # , object_pairs_hook=OrderedDict
                except brotli.error:
                    output_dict = json.loads(compr_bytes.decode("utf-8")) # , object_pairs_hook=OrderedDict

            # remove some keys in input not written by the vt writer ?
            self.__remove_non_applicable_keys_from_input_data(input_dict)
            # remove non comparable key ? (meta vs type)
            self.__remove_non_applicable_keys_from_output_data(output_dict)

            # sort phases and entities by id ?
            self.__sort_data(input_dict)
            self.__sort_data(output_dict)

            # validate output against the JSON schema validator
            self.assertTrue(
                SchemaValidator(schema_type="LBDatafile").is_valid(schema_to_validate=output_dict),
                f"Invalid JSON schema in {output_file_name}"
            )

            print(f"-------------------------------{input_file_name}-----------------------------------")
            print(json.dumps(input_dict, indent=4, sort_keys = True, ))
            print(f"-------------------------------{output_file_name}----------------------------------")
            print(json.dumps(output_dict, indent=4, sort_keys = True))
            print("-----------------------------------------------------------------------")

            self.maxDiff = None
            self.assertDictEqual(input_dict, output_dict)


if __name__ == "__main__":
    unittest.main()
