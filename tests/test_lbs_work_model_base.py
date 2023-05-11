import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

import logging
import unittest

from src.lbaf.Model.lbsWorkModelBase import WorkModelBase


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            raise SystemExit(1)
        self.logger = logging.getLogger()

    def test_lbs_work_model_base_factory(self):
        with self.assertRaises(NameError) as err:
            WorkModelBase.factory("Not a good name", parameters={}, lgr=self.logger)
        self.assertEqual(err.exception.args[0], "Could not create a work with name: Not a good name")


if __name__ == '__main__':
    unittest.main()
