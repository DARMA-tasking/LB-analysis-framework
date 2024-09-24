#
#@HEADER
###############################################################################
#
#                        test_json_data_files_maker.py
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
import os
import unittest
from unittest.mock import patch
import argparse
from typing import Callable


from src.lbaf.Utils.lbsJSONDataFilesMaker import JSONDataFilesMaker

class TestJsonDataFilesMaker(unittest.TestCase):

    test_dir: str = os.path.dirname(os.path.dirname(__file__))
    config_dir: str = os.path.join(test_dir, "config", "phases")
    output_dir: str = os.path.join(test_dir, "output", "JSON_data_files_maker")

    argparse_args: Callable[..., argparse.Namespace] = lambda **kwargs: argparse.Namespace(
        spec_file=kwargs.get("spec_file"),
        data_stem=kwargs.get("data_stem"),
        interactive=kwargs.get("interactive", False),
        multiple_sharing=kwargs.get("multiple_sharing", False),
        output_config_file=kwargs.get("output_config_file", None),
        compressed=False
    )

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_01_wrong.yaml"),
        data_stem=os.path.join(output_dir, "dataset01")
    ))
    def test_make_data_files_from_spec_wrong_01(self, _namespace: argparse.Namespace):
        """Test that invalid phase configuration 01 generates no dataset and fire error"""

        with self.assertRaises(SystemExit) as err:
            JSONDataFilesMaker().run()
        self.assertEqual(err.exception.__context__.args[0],
            "Cannot assign task 1 to rank 1. It is already assigned to rank 0")

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_02_wrong.yaml"),
        data_stem=os.path.join(output_dir, "dataset02")
    ))
    def test_make_data_files_from_spec_wrong_02(self, _namespace: argparse.Namespace):
        """Test that invalid phase configuration 02 generates no dataset and fire error"""

        with self.assertRaises(SystemExit) as err:
            JSONDataFilesMaker().run()
        self.assertEqual(err.exception.__context__.args[0],
            "Task 0 already shared block 0 and cannot share additional block 2. Only 0 or 1 allowed"
        )

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_03_valid.yaml"),
        data_stem=os.path.join(output_dir, "dataset03")
    ))
    def test_make_data_files_from_spec_valid_03(self, namespace: argparse.Namespace):
        """Test that valid phase configuration correctly generates a dataset"""

        print(namespace)
        JSONDataFilesMaker().run()

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_04_valid.yaml"),
        data_stem=os.path.join(output_dir, "dataset04")
    ))
    def test_make_data_files_from_spec_valid_04(self, namespace: argparse.Namespace):
        """Test that valid phase configuration with tasks from different ranks shared same block correctly generates a dataset"""

        print(namespace)
        JSONDataFilesMaker().run()

    @patch('argparse.ArgumentParser.parse_args', return_value=argparse_args(
        spec_file=os.path.join(config_dir, "phase_spec_05_valid.yaml"),
        data_stem=os.path.join(output_dir, "dataset05")
    ))
    def test_make_data_files_from_spec_valid_05(self, namespace: argparse.Namespace):
        """Test that valid phase configuration using dict and not lists correctly generates a dataset"""

        print(namespace)
        JSONDataFilesMaker().run()


if __name__ == "__main__":
    unittest.main()
