import os
import sys
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
        #Instantiate the logger
        self.logger = logging.getLogger()

        # Define the work model and criterion
        self.work_model = WorkModelBase.factory(
            "AffineCombination",
            {"deterministic_transfer": "true"},
            self.logger)
        self.criterion = CriterionBase.factory(
            "Tempered",
            self.work_model,
            self.logger)

        # Define objects and add them to a memory block
        self.migratable_objects = {Object(i=0, load=1.0), Object(i=1, load=0.5), Object(i=2, load=0.5), Object(i=3, load=0.5)}
        self.sentinel_objects = {Object(i=15, load=4.5), Object(i=18, load=2.5)}
        self.block = Block(b_id=0,h_id=0)
        self.block_set = {self.block}
        for o in self.migratable_objects:
          o.set_shared_block(self.block)
          self.block.attach_object_id(o.get_id())

        # Define the rank and declare known peers
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
        self.rank.set_shared_blocks(self.block_set)
        self.known_peers = {}

        # Instantiate the reader
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.test_dir, "data")
        self.file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_compressed", "data")
        self.reader = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix="json")

        # Instantiate the phase
        self.phase = Phase(self.logger, 0, reader=self.reader)
        self.phase.set_ranks([self.rank])
        self.criterion.set_phase(self.phase)

        # Finally, create instance of Clustering Transfer Strategy
        self.clustering_transfer_strategy=ClusteringTransferStrategy(criterion=self.criterion, parameters={}, lgr=self.logger)

    def test_lbs_clustering_transfer_strategy_build_rank_clusters(self):
        expected_output = {
        None: [],
        self.block.get_id(): [
            Object(i=0, load=1.0),
            Object(i=1, load=0.5),
            Object(i=2, load=0.5),
            Object(i=3, load=0.5),
          ]
        }
        self.assertCountEqual(
          self.clustering_transfer_strategy._ClusteringTransferStrategy__build_rank_clusters(self.rank, with_nullset=True),
          expected_output)

    def test_lbs_clustering_transfer_strategy_build_rank_subclusters(self):
        clusters = self.clustering_transfer_strategy._ClusteringTransferStrategy__build_rank_clusters(self.rank, with_nullset=False).values()
        print(clusters)
        for i, v in enumerate(clusters):
          print(f"i: {i}, v: {v}")
        rank_load = self.rank.get_load()

        # Functionality is tested with execute()
        assert isinstance(
          self.clustering_transfer_strategy._ClusteringTransferStrategy__build_rank_subclusters(clusters, rank_load),
          list
        )

    def test_lbs_clustering_transfer_strategy_no_suitable_subclusters(self):
        clusters = None
        rank_load = self.rank.get_load()
        self.assertEqual(
          self.clustering_transfer_strategy._ClusteringTransferStrategy__build_rank_subclusters(clusters, rank_load),
          []
        )

    def test_lbs_clustering_transfer_strategy_execute_cluster_swaps(self):

      # Establish known_peers
      rank_list = [self.rank] # Make rank aware of itself

      # Populate self.known_peers
      for i in range(4):
        rank_list.append(Rank(r_id=i, logger=self.logger))
      self.known_peers = {self.rank: set(rank_list)}

      # Define ave_load (2.5 / 4)
      ave_load = 0.6

      # Assertions
      self.assertEqual(
        self.clustering_transfer_strategy.execute(known_peers=self.known_peers,
                                                  phase=self.phase,
                                                  ave_load=ave_load),
        (0,len(rank_list) - 1,0)
      )


if __name__ == "__main__":
    unittest.main()
