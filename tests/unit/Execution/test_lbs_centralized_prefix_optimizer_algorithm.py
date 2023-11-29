# import logging
# import random
# import unittest
# from unittest.mock import patch

# from src.lbaf.Model.lbsMessage import Message
# from src.lbaf.Model.lbsObject import Object
# from src.lbaf.Model.lbsRank import Rank
# from src.lbaf.Execution.lbsClusteringTransferStrategy import ClusteringTransferStrategy
# from src.lbaf.Model.lbsWorkModelBase import WorkModelBase

# class TestConfig(unittest.TestCase):
#   def setUp(self):
#     self.logger = logging.getLogger()
#     # self.migratable_objects = {Object(i=0, load=1.0), Object(i=1, load=0.5), Object(i=2, load=0.5), Object(i=3, load=0.5)}
#     # self.sentinel_objects = {Object(i=15, load=4.5), Object(i=18, load=2.5)}
#     # self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
#     self.central_pref_opt_alg = ClusteringTransferStrategy(
#         work_model=WorkModelBase(),
#         parameters={
#             "n_iterations": 8,
#             "n_rounds": 4,
#             "fanout": 4,
#             "order_strategy": "arbitrary",
#             "criterion": "Tempered",
#             "skip_transfer": True,
#             "max_objects_per_transfer": 8,
#             "deterministic_transfer": True
#         },
#         lgr=self.logger,
#         rank_qoi=None,
#         object_qoi=None)

#     self.brute_force = ClusteringTransferStrategy(
#         work_model=WorkModelBase(),
#         parameters={
#             "n_iterations": 8,
#             "n_rounds": 4,
#             "fanout": 4,
#             "order_strategy": "arbitrary",
#             "criterion": "Tempered",
#             "max_objects_per_transfer": 8,
#             "deterministic_transfer": True
#         },
#         lgr=self.logger,
#         rank_qoi=None,
#         object_qoi=None)

#   def test_lbs_central_pref_opt_alg(self):
#       assert self.central_pref_opt_alg.execute()

# if __name__ == "__main__":
#     unittest.main()
