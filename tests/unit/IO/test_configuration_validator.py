#
#@HEADER
###############################################################################
#
#                       test_configuration_validator.py
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
from schema import SchemaError, SchemaMissingKeyError, SchemaOnlyOneAllowedError
import yaml

from src.lbaf.Utils.lbsPath import abspath
from src.lbaf.IO.lbsConfigurationValidator import ConfigurationValidator
from src.lbaf.Utils.lbsLogging import get_logger


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.config_dir = os.path.join(self.test_dir, "config")

    def test_config_validator_correct_001(self):
        with open(os.path.join(self.config_dir, "conf_correct_001.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_correct_002(self):
        with open(os.path.join(self.config_dir, "conf_correct_002.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_correct_003(self):
        with open(os.path.join(self.config_dir, "conf_correct_003.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_wrong_data_and_sampling(self):
        with open(os.path.join(self.config_dir, "conf_wrong_data_and_sampling.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaOnlyOneAllowedError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0],"There are multiple keys present from the Or('from_data', 'from_samplers') condition")

    def test_config_validator_wrong_no_data_and_sampling(self):
        with open(os.path.join(self.config_dir, "conf_wrong_no_data_and_sampling.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: Or('from_data', 'from_samplers')")

    def test_config_validator_wrong_missing_from_data_phase(self):
        with open(os.path.join(self.config_dir, "conf_wrong_missing_from_data_param.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: 'phase_ids'")

    def test_config_validator_wrong_from_data_phase_type(self):
        with open(os.path.join(self.config_dir, "conf_wrong_from_data_phase_type.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'list' of 'int' types")

    def test_config_validator_wrong_from_data_phase_name(self):
        with open(os.path.join(self.config_dir, "conf_wrong_from_data_phase_name.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: 'phase_ids'")

    def test_config_validator_wrong_work_model_missing(self):
        with open(os.path.join(self.config_dir, "conf_wrong_work_model_missing.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: 'work_model'")

    def test_config_validator_wrong_work_model_name(self):
        with open(os.path.join(self.config_dir, "conf_wrong_work_model_name.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "LoadOnly or AffineCombination must be chosen")

    def test_config_validator_wrong_work_model_parameters_missing(self):
        with open(os.path.join(self.config_dir, "conf_wrong_work_model_parameters_missing.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Key 'work_model' error:\nKey 'parameters' error:\n"
                                                "Missing key: 'beta'")

    def test_config_validator_wrong_work_model_parameters_type(self):
        with open(os.path.join(self.config_dir, "conf_wrong_work_model_parameters_type.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Key 'work_model' error:\nKey 'parameters' error:\nKey 'beta' error:\n"
                                                "'0.' should be instance of 'float'")

    def test_config_validator_wrong_from_samplers_load_sampler_001(self):
        with open(os.path.join(self.config_dir, "conf_wrong_from_samplers_load_sampler_001.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "There should be exactly 2 provided parameters of type 'float'")

    def test_config_validator_wrong_from_samplers_load_sampler_002(self):
        with open(os.path.join(self.config_dir, "conf_wrong_from_samplers_load_sampler_002.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "There should be exactly 2 provided parameters of type 'float'")

    def test_config_validator_wrong_from_samplers_load_sampler_003(self):
        with open(os.path.join(self.config_dir, "conf_wrong_from_samplers_load_sampler_003.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "There should be exactly 2 provided parameters of type 'float'")

    def test_config_validator_wrong_from_samplers_load_sampler_004(self):
        with open(os.path.join(self.config_dir, "conf_wrong_from_samplers_load_sampler_004.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "uniform or lognormal must be chosen")

    def test_config_validator_wrong_from_samplers_load_sampler_005(self):
        with open(os.path.join(self.config_dir, "conf_wrong_from_samplers_load_sampler_005.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: 'load_sampler'")

    def test_config_validator_correct_from_samplers_no_logging_level(self):
        with open(os.path.join(self.config_dir, "conf_correct_from_samplers_no_ll.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_correct_brute_force(self):
        with open(os.path.join(self.config_dir, "conf_correct_brute_force.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_from_data_min_config(self):
        with open(os.path.join(self.config_dir, "conf_correct_from_data_min_config.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_from_data_algorithm_invalid_001(self):
        with open(os.path.join(self.config_dir, "conf_wrong_algorithm_invalid_001.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Key 'parameters' error:\nMissing key: 'skip_transfer'")

    def test_config_from_data_algorithm_invalid_002(self):
        with open(os.path.join(self.config_dir, "conf_wrong_algorithm_invalid_002.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Key 'parameters' error:\nMissing key: 'fanout'")

    def test_config_validator_correct_phase_ids_str_001(self):
        with open(os.path.join(self.config_dir, "conf_correct_phase_ids_str_001.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_wrong_phase_ids_str_001(self):
        with open(os.path.join(self.config_dir, "conf_wrong_phase_ids_str_001.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'list' of 'int' types")

    def test_config_validator_correct_clustering(self):
        with open(os.path.join(self.config_dir, "conf_correct_clustering.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_correct_clustering_set_tol(self):
        with open(os.path.join(self.config_dir, "conf_correct_clustering_set_tol.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_wrong_clustering_set_tol_type(self):
        with open(os.path.join(self.config_dir, "conf_wrong_clustering_set_tol_type.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'float' and > 0.0")

    def test_config_validator_wrong_clustering_set_tol_mag(self):
        with open(os.path.join(self.config_dir, "conf_wrong_clustering_set_tol_mag.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'float' and > 0.0")

    def test_config_validator_correct_clustering_target_imb(self):
        with open(os.path.join(self.config_dir, "conf_correct_clustering_target_imb.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_wrong_max_subclusters_type(self):
        with open(os.path.join(self.config_dir, "conf_wrong_max_subclusters_type.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'int' and >= 0")

    def test_config_validator_wrong_max_subclusters_mag(self):
        with open(os.path.join(self.config_dir, "conf_wrong_max_subclusters_mag.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'int' and >= 0")

    def test_config_validator_wrong_separate_subclustering(self):
        with open(os.path.join(self.config_dir, "conf_wrong_separate_subclustering.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Key 'parameters' error:\nKey 'separate_subclustering' error:\n'incorrect' should be instance of 'bool'")

    def test_config_validator_correct_subclustering_filters(self):
        with open(os.path.join(self.config_dir, "conf_correct_subclustering_filters.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()

    def test_config_validator_wrong_subclustering_minimum_improvement(self):
        with open(os.path.join(self.config_dir, "conf_wrong_subclustering_minimum_improvement.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'float' and >= 0.0")

    def test_config_validator_wrong_subclustering_threshold(self):
        with open(os.path.join(self.config_dir, "conf_wrong_subclustering_threshold.yml"), "rt", encoding="utf-8") as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=get_logger()).main()
        self.assertEqual(err.exception.args[0], "Should be of type 'float' and >= 0.0")

if __name__ == "__main__":
    unittest.main()
