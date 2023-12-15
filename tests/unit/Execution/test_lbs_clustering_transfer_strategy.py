import os
import sys
import logging
import unittest

from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsBlock import Block
from src.lbaf.Model.lbsObject import Object
from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.IO.lbsVTDataWriter import VTDataWriter
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
            {},
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

       # Instantiate the phase
        self.phase = Phase(lgr=self.logger, p_id=0)
        self.phase.set_ranks([self.rank])
        self.criterion.set_phase(self.phase)

        # Finally, create instance of Clustering Transfer Strategy
        self.clustering_transfer_strategy = ClusteringTransferStrategy(criterion=self.criterion, parameters={"deterministic_transfer": True}, lgr=self.logger)

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

        self.assertEqual(
            self.clustering_transfer_strategy.execute(known_peers=self.known_peers,
                                                      phase=self.phase,
                                                      ave_load=ave_load),
            (0,len(rank_list) - 1,0)
        )

    def test_lbs_clustering_transfer_strategy_iterate_subclusters(self):
        # Create suitable objects
        obj0 = Object(i=0, load=89.0)
        obj1 = Object(i=1, load=1.0)
        obj2 = Object(i=2, load=9.0)
        obj3 = Object(i=3, load=94.0)
        obj4 = Object(i=4, load=1.0)
        obj5 = Object(i=5, load=6.0)

        # Create memory blocks
        r_id0 = 0
        r_id1 = 1
        block0 = Block(b_id=0, h_id=r_id0, size=1.0, o_ids={o.get_id() for o in [obj0, obj1]})
        block1 = Block(b_id=1, h_id=r_id0, size=1.0, o_ids={obj2.get_id()})
        block2 = Block(b_id=2, h_id=r_id1, size=1.0, o_ids={o.get_id() for o in [obj3, obj4]})
        block3 = Block(b_id=3, h_id=r_id1, size=1.0, o_ids={obj5.get_id()})

        # Assign objects to memory blocks
        obj0.set_shared_block(block0)
        obj1.set_shared_block(block0)

        obj2.set_shared_block(block1)

        obj3.set_shared_block(block2)
        obj4.set_shared_block(block2)

        obj5.set_shared_block(block3)

        # Set up initial configuration
        rank0 = Rank(r_id=r_id0, mo={obj0, obj1, obj2}, logger=self.logger)
        rank1 = Rank(r_id=r_id1, mo={obj3, obj4, obj5}, logger=self.logger)

        # Assign ranks to memory blocks
        rank0.set_shared_blocks({block0, block1})
        rank1.set_shared_blocks({block2, block3})

        # Create known_peers set
        rank_list = [rank0, rank1]
        known_peers = {}
        for r in rank_list:
            known_peers[r] = set(rank_list)

        # Instantiate the phase
        phase = Phase(lgr=self.logger, p_id=1)
        phase.set_ranks([r for r in known_peers])

        # Find testing output dir
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "subclustering_test")

        # Create writer
        writer = VTDataWriter(
            self.logger,
            output_dir,
            "subclustering",
            {"json_output_suffix" : "json",
             "compressed": False}
        )

        # Create criterion
        criterion = CriterionBase.factory(
            "Tempered",
            self.work_model,
            self.logger)
        criterion.set_phase(phase)

        # Identify all parameters
        params = {
            "deterministic_transfer": True,
            "fanout": 1,
            "n_rounds": 1}
        non_det_params = {
            "deterministic_transfer": False,
            "fanout": 1,
            "n_rounds": 1}

        # Define ave_load
        ave_load = 100

        # Create instance of Clustering Transfer Strategy
        clustering_transfer_strategy=ClusteringTransferStrategy(criterion=criterion, parameters=params, lgr=self.logger)
        clustering_transfer_strategy_non_det=ClusteringTransferStrategy(criterion=criterion, parameters=non_det_params, lgr=self.logger)

        # Test that non deterministic execute function runs
        assert isinstance(
            clustering_transfer_strategy_non_det.execute(known_peers=known_peers,
                                                 phase=phase,
                                                 ave_load=ave_load),
            tuple)

        # Test that deterministic execute function is as expected
        self.assertEqual(
            clustering_transfer_strategy.execute(
                                                 known_peers=known_peers,
                                                 phase=phase,
                                                 ave_load=ave_load),
            (0,1,2))

        # If successful, write out problem to JSON
        writer.write({phase.get_id(): phase})

if __name__ == "__main__":
    unittest.main()
