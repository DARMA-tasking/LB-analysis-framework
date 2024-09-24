#
#@HEADER
###############################################################################
#
#                           test_lbs_work_models.py
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
        self.migratable_objects = {Object(seq_id=0, load=1.0), Object(seq_id=1, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=3, load=0.5)}
        self.sentinel_objects = {Object(seq_id=15, load=4.5), Object(seq_id=18, load=2.5)}
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
