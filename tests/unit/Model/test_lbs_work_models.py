import os
import logging
import unittest

from src.lbaf import PROJECT_PATH
from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(PROJECT_PATH, "tests", "data")
        self.logger = logging.getLogger()
        self.migratable_objects = {Object(i=0, load=1.0), Object(i=1, load=0.5), Object(i=2, load=0.5), Object(i=3, load=0.5)}
        self.sentinel_objects = {Object(i=15, load=4.5), Object(i=18, load=2.5)}
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
        self.rank_load = self.rank.get_load()

    def test_lbs_work_model_base_factory(self):
        with self.assertRaises(NameError) as err:
            WorkModelBase.factory("Not a good name", parameters={}, lgr=self.logger)
        self.assertEqual(err.exception.args[0], "Could not create a work with name: Not a good name")

    def test_lbs_load_only_work_model(self):
        load_only_work_model = WorkModelBase.factory("LoadOnly", parameters={}, lgr=self.logger)
        self.assertEqual(load_only_work_model.compute(self.rank),
                         self.rank_load)

    def test_lbs_affine_combination_work_model(self):
        alpha = 1.0
        beta = 1.0
        gamma = 1.0
        upper_bounds_dict = {}
        upper_bounds_dict["max_memory_usage"] = 8.0e+9
        affine_params = {"alpha": alpha,
                         "beta": beta,
                         "gamma": gamma,
                         "upper_bounds": upper_bounds_dict}

        affine_combination_work_model = WorkModelBase.factory("AffineCombination", parameters=affine_params, lgr=self.logger)
        self.assertEqual(affine_combination_work_model.get_alpha(),
                         alpha)
        self.assertEqual(affine_combination_work_model.get_beta(),
                         beta)
        self.assertEqual(affine_combination_work_model.get_gamma(),
                         gamma)
        self.assertEqual(affine_combination_work_model.compute(self.rank),
                        self.rank_load + max(self.rank.get_received_volume(), self.rank.get_sent_volume()) + 1.0)

if __name__ == "__main__":
    unittest.main()
