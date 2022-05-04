import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    exit(1)

from schema import SchemaError, SchemaMissingKeyError, SchemaOnlyOneAllowedError, SchemaUnexpectedTypeError
import unittest
import yaml

from src.lbaf.IO.configurationValidator import ConfigurationValidator
from src.lbaf.Utils.logger import logger


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.config_dir = os.path.join(
                f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data', 'config')
            sys.path.append(self.config_dir)
        except Exception as e:
            print(f"Can not add config path to system path! Exiting!\nERROR: {e}")
            exit(1)

    def test_config_validator_correct_001(self):
        with open(os.path.join(self.config_dir, 'conf_correct_001.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()

    def test_config_validator_correct_002(self):
        with open(os.path.join(self.config_dir, 'conf_correct_002.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()

    def test_config_validator_correct_003(self):
        with open(os.path.join(self.config_dir, 'conf_correct_003.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)
        ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()

    def test_config_validator_wrong_data_and_sampling(self):
        with open(os.path.join(self.config_dir, 'conf_wrong_data_and_sampling.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaOnlyOneAllowedError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()
        self.assertEqual(err.exception.args[0],
                         "There are multiple keys present from the Or('from_data', 'from_samplers') condition")

    def test_config_validator_wrong_no_data_and_sampling(self):
        with open(os.path.join(self.config_dir, 'conf_wrong_no_data_and_sampling.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: Or('from_data', 'from_samplers')")

    def test_config_validator_wrong_missing_from_data_phase(self):
        with open(os.path.join(self.config_dir, 'conf_wrong_missing_from_data_param.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: 'phase_id'")

    def test_config_validator_wrong_from_data_phase_type(self):
        with open(os.path.join(self.config_dir, 'conf_wrong_from_data_phase_type.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()
        self.assertEqual(err.exception.args[0], "Key 'phase_id' error:\n0.0 should be instance of 'int'")

    def test_config_validator_wrong_from_data_phase_name(self):
        with open(os.path.join(self.config_dir, 'conf_wrong_from_data_phase_name.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: 'phase_id'")

    def test_config_validator_wrong_work_model_missing(self):
        with open(os.path.join(self.config_dir, 'conf_wrong_work_model_missing.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaMissingKeyError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()
        self.assertEqual(err.exception.args[0], "Missing key: 'work_model'")

    def test_config_validator_wrong_work_model_name(self):
        with open(os.path.join(self.config_dir, 'conf_wrong_work_model_name.yml'), 'rt') as config_file:
            yaml_str = config_file.read()
            configuration = yaml.safe_load(yaml_str)

        with self.assertRaises(SchemaError) as err:
            ConfigurationValidator(config_to_validate=configuration, logger=logger()).main()
        self.assertEqual(err.exception.args[0], "LoadOnly or AffineCombination needs to be chosen")


if __name__ == '__main__':
    unittest.main()
