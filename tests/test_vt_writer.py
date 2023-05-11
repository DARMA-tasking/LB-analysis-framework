"""Tests for the VT Writer"""
import os
import sys
import unittest
import filecmp
import shutil
import brotli
import json
import subprocess
import yaml

from lbaf.Utils.common import current_dir, project_dir, abspath_from, project_dir
from lbaf.Utils.logger import logger
from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.IO.lbsVTDataWriter import VTDataWriter
from lbaf.Model.lbsPhase import Phase
from collections import OrderedDict 

# pylint:disable=C0115,C0116,W0212(protected-access)

# TODO: Test VT WRITER
class TestVTDataWriter(unittest.TestCase):
    ouput_dir: str
    """Test class for VTDataWriter"""
    def setUp(self):
        self.output_dir = current_dir() + '/output/vt_writer'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def tearDown(self):
        # shutil.rmtree(self.output_dir)
        return

    # def test_run_lbaf(self):
    #     """Test that LBAF runs correctly with demo configuration file at config/conf.yaml"""
    #     lbaf_path = os.path.join(project_dir(), 'src', 'lbaf', 'Applications', 'LBAF_app.py')
    #     lbaf_config_file = os.path.join(project_dir(), 'config', 'conf.yaml')
    #     lbaf_run = subprocess.run(
    #         [
    #             sys.executable,
    #             lbaf_path,
    #             '-c',
    #             lbaf_config_file
    #         ],
    #         check=True,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.STDOUT
    #     )
    #     self.assertEqual(0, lbaf_run.returncode)

    # def test_vt_writer_run(self):
    #     """Test that vt files are exactly the identical to the input data when using the VT writer
    #     1. read in the VT data in  data_stem: ../data/challenging_toy_fewer_tasks/toy;
    #     2. execute LBAF using, e.g., 0 iterations of the phase stepper algorithm;
    #     3. write the VT output data files and verify those exactly identical to the input data.
    #     """
        
    #     lbaf_path = os.path.join(project_dir(), 'src', 'lbaf', 'Applications', 'LBAF_app.py')
    #     lbaf_config_dir = os.path.join(current_dir(), 'config')
    #     lbaf_config_file = os.path.join(lbaf_config_dir, 'conf_correct_vt_writer.yml')
    #     lbaf_config = {}
    #     with open(lbaf_config_file, "rt", encoding="utf-8") as lbaf_config_io:
    #         lbaf_config = yaml.safe_load(lbaf_config_io.read())
    #     lbaf_output_dir = abspath_from(lbaf_config.get('output_dir'), lbaf_config_dir)
    #     lbaf_run = subprocess.run(
    #         [
    #             sys.executable,
    #             lbaf_path,
    #             '-c',
    #             lbaf_config_file
    #         ],
    #         check=True,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.STDOUT
    #     )

    #     # check that lbaf has run correctly
    #     # self.assertEqual(0, lbaf_run.returncode)

    #     # check that expected output files exists and content is same than input files
    #     # get some info from the config file
    #     data_stem = lbaf_config.get('from_data').get('data_stem')
    #     lbaf_input_dir = f"{os.sep}".join(data_stem.split(os.sep)[:-1])
    #     lbaf_input_dir = abspath_from(lbaf_input_dir, lbaf_config_dir)
    #     input_file_prefix = data_stem.split(os.sep)[-1]
    #     n_ranks = len([name for name in os.listdir(lbaf_input_dir)])
    #     output_file_prefix = lbaf_config.get('output_file_stem')
    #     for i in range(0, n_ranks):
    #         input_file_name = f"{input_file_prefix}.{i}.json"
    #         input_file = os.path.join(lbaf_input_dir, input_file_name)
    #         output_file_name = f"{output_file_prefix}.{i}.vom"
    #         output_file = os.path.join(lbaf_output_dir, output_file_name)

    #         # check output file exists
    #         self.assertTrue(
    #             os.path.isfile(output_file),
    #             f'File {output_file_name} not generated at {lbaf_output_dir}')

    #         # check output file contains the same content than the input file
    #         input_file_content = ""
    #         with open(input_file, "rt", encoding="utf-8") as input_file_io:
    #             input_file_content = input_file_io.read()
    #         output_file_content = ""
    #         with open(output_file, 'rb') as output_file_io:
    #             output_file_content = output_file_io.read()
    #             output_file_content = brotli.decompress(output_file_content)
    #             output_file_content = output_file_content.decode('utf-8')

    #         print("--------------------")
    #         print(input_file_content)
    #         print("--------------------")
    #         print(output_file_content)
    #         print("--------------------")

    #         input_file_data = json.loads(input_file_content)
    #         output_file_data = json.loads(output_file_content)
    #         print("--------------------")
    #         print(input_file_data)
    #         print("--------------------")
    #         print(output_file_data)
    #         print("--------------------")

    #         self.assertEqual(input_file_content, output_file_content)

    # def test_vt_writer_run(self):
    #     # reader reads a file
    #     # writer writes a file
    #     # compare

    def _run(self, config_file) -> subprocess.CompletedProcess:
        """Runs LBAF as a subprocess
        """

        lbaf_path = os.path.join(project_dir(), 'src', 'lbaf', 'Applications', 'LBAF_app.py')
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

    def test_vt_writer_null_test_valid_output(self):
        # run LBAF with a null test
        config_file = os.path.join(os.path.dirname(__file__), 'config', 'conf_vt_writer_null_test.yml')
        proc = self._run(config_file)
        self.assertEqual(0, proc.returncode)

        # check output
        with open(config_file, "rt", encoding="utf-8") as file_io:
            config = yaml.safe_load(file_io)
        data_stem = config.get('from_data').get('data_stem')
        input_dir = f"{os.sep}".join(data_stem.split(os.sep)[:-1])
        input_dir = abspath_from(input_dir, os.path.dirname(config_file))
        input_file_prefix = data_stem.split(os.sep)[-1]
        n_ranks = len([name for name in os.listdir(input_dir)])
        output_file_prefix = config.get('output_file_stem')
        output_dir = abspath_from(config.get("output_dir", '.'), os.path.dirname(config_file))

        for i in range(0, n_ranks):
            input_file_name = f"{input_file_prefix}.{i}.json"
            input_file = os.path.join(input_dir, input_file_name)
            output_file_name = f"{output_file_prefix}.{i}.json"
            output_file = os.path.join(output_dir, output_file_name)

            # check output file exists
            self.assertTrue(
                os.path.isfile(output_file),
                f'File {output_file} not generated at {output_dir}')

            # check output file contains the same content than the input file
            input_file_content = ""
            with open(input_file, "rt", encoding="utf-8") as input_file_io:
                input_file_content = input_file_io.read()
            output_file_content = ""
            with open(output_file, 'rb') as output_file_io:
                output_file_content = output_file_io.read()
                output_file_content = brotli.decompress(output_file_content)
                output_file_content = output_file_content.decode('utf-8')

            input_dict = json.loads(input_file_content, object_pairs_hook=OrderedDict)
            output_dict = json.loads(output_file_content, object_pairs_hook=OrderedDict)

            print(f"-------------------------------{input_file_name}-----------------------------------")
            print(json.dumps(input_dict, indent=4, sort_keys = True))
            print(f"-------------------------------{output_file_name}----------------------------------")
            print(json.dumps(output_dict, indent=4, sort_keys = True))
            print("-----------------------------------------------------------------------")

            self.maxDiff = None
            self.assertDictEqual(input_dict, output_dict)
