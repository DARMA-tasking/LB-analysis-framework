import os
import logging
import unittest

from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsBlock import Block
from src.lbaf.Model.lbsObject import Object
from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase
from src.lbaf.Execution.lbsCriterionBase import CriterionBase
from src.lbaf.Execution.lbsClusteringTransferStrategy import ClusteringTransferStrategy


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.work_model = WorkModelBase.factory(
            "AffineCombination",
            {},
            self.logger)
        self.criterion = CriterionBase.factory(
            "Tempered",
            self.work_model,
            self.logger
        )
        self.migratable_objects = {Object(i=0, load=1.0), Object(i=1, load=0.5), Object(i=2, load=0.5), Object(i=3, load=0.5)}
        self.sentinel_objects = {Object(i=15, load=4.5), Object(i=18, load=2.5)}
        self.block = Block(b_id=0,h_id=0)
        for o in self.migratable_objects:
          o.set_shared_block(self.block)
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
        self.known_peers = {}
        self.known_peers[self.rank] = {self.rank}
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.test_dir, "data")
        self.file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_compressed", "data")
        self.reader = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix="json")
        self.phase = Phase(self.logger, 0, reader=self.reader)
        self.phase.set_ranks([self.rank])
        self.clustering_transfer_strategy=ClusteringTransferStrategy(criterion=self.criterion, parameters={}, lgr=self.logger)

    def test_lbs_clustering_transfer_strategy_cluster_objects(self):
        expected_output = {
          None: [],
          self.block.get_id(): [
              Object(i=0, load=1.0),
              Object(i=1, load=0.5),
              Object(i=2, load=0.5),
              Object(i=3, load=0.5),
          ],
        }
        self.assertCountEqual(
          self.clustering_transfer_strategy._ClusteringTransferStrategy__cluster_objects(self.rank),
          expected_output
        )

    def test_lbs_clustering_transfer_strategy_find_suitable_subclusters(self):
        clusters = self.clustering_transfer_strategy._ClusteringTransferStrategy__cluster_objects(self.rank)
        rank_load = self.rank.get_load()

        # Functionality is tested with execute()
        assert isinstance(
          self.clustering_transfer_strategy._ClusteringTransferStrategy__find_suitable_subclusters(clusters, rank_load),
          list
        )

    def test_lbs_clustering_transfer_strategy_no_suitable_subclusters(self):
        clusters = None
        rank_load = self.rank.get_load()
        self.assertEqual(
          self.clustering_transfer_strategy._ClusteringTransferStrategy__find_suitable_subclusters(clusters, rank_load),
          []
        )

    def test_lbs_clustering_transfer_strategy_execute(self):
      # temp_1_migratable_objects = {Object(i=0, load=2.0), Object(i=1, load=2.5), Object(i=2, load=1.5), Object(i=3, load=3.5)}
      # temp_2_migratable_objects = {Object(i=0, load=3.0), Object(i=1, load=1.5), Object(i=2, load=2.5), Object(i=3, load=1.5)}
      temp_rank_1 = Rank(r_id=1, logger=self.logger)
      temp_rank_2 = Rank(r_id=2, logger=self.logger)
      rank_list = [temp_rank_1, temp_rank_2]
      for rank in rank_list:
        self.known_peers[rank] = {rank}
      ave_load = 5.0

      self.assertEqual(
        self.clustering_transfer_strategy.execute(self.known_peers, self.phase, ave_load)[0],
        4, 0, 0
      )


if __name__ == "__main__":
    unittest.main()
