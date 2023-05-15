import os
import logging
import unittest

from lbaf import PROJECT_PATH
from lbaf.Model.lbsWorkModelBase import WorkModelBase


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(PROJECT_PATH, "tests", "data")
        self.logger = logging.getLogger()

    def test_lbs_work_model_base_factory(self):
        with self.assertRaises(NameError) as err:
            WorkModelBase.factory("Not a good name", parameters={}, lgr=self.logger)
        self.assertEqual(err.exception.args[0], "Could not create a work with name: Not a good name")


if __name__ == "__main__":
    unittest.main()
