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
from src.lbaf.Model.lbsObjectCommunicator import ObjectCommunicator
from src.lbaf.Execution.lbsRecursiveTransferStrategy import RecursiveTransferStrategy


class TestConfig(unittest.TestCase):
    def setUp(self):
        #Instantiate the logger
        self.logger = logging.getLogger()

        self.params = {"order_strategy":"increasing_loads"}

        # Define the work model and criterion
        self.work_model = WorkModelBase.factory(
            "AffineCombination",
            self.params,
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

        # Finally, create instance of Recursive Transfer Strategy
        self.recursive_transfer_strategy=RecursiveTransferStrategy(criterion=self.criterion, parameters=self.params, logger=self.logger)

    def test_recursive_transfer_strategy_orderings(self):

        # Set up all order strategies
        order_strategy_list = ["arbitrary", "element_id", "decreasing_loads", "increasing_loads",
                               "increasing_connectivity", "fewest_migrations", "small_objects"]

        param_dict = {}

        # Set up objects
        # Establish communications
        rec_object_min = {Object(i=7, load=0.5): 5.0}
        rec_object_max = {Object(i=8, load=1.0): 10.0}
        sent_object_min = {Object(i=9, load=0.5): 6.0}
        sent_object_max = {Object(i=10, load=1.0): 12.0}

        # Create objects
        obj_04 = Object(i=4, load=5.0, comm=ObjectCommunicator(i=4,logger=self.logger,r=rec_object_max, s=sent_object_max))
        obj_05 = Object(i=5, load=3.0, comm=ObjectCommunicator(i=5,logger=self.logger,r=rec_object_min, s=sent_object_min))
        obj_06 = Object(i=6, comm=None)

        # Define objects set
        objects = [
          obj_04,
          obj_05,
          obj_06
        ]

        objects_reverse = [
            obj_06,
            obj_05,
            obj_04
        ]

        expected_order_dict = {
            "arbitrary": list(objects),
            "element_id": list(objects),
            "decreasing_loads": list(objects),
            "increasing_loads": list(objects_reverse),
            "increasing_connectivity": list(objects_reverse),
            "fewest_migrations": list(objects),
            "small_objects": list(objects)
        }

        for order_strategy in order_strategy_list:
            param_dict["order_strategy"] = order_strategy
            recursive_strat = RecursiveTransferStrategy(criterion=self.criterion, parameters=param_dict, logger=self.logger)
            self.assertEqual(f"{order_strategy}: {getattr(recursive_strat, order_strategy)(objects, 0)}",
                             f"{order_strategy}: {expected_order_dict[f'{order_strategy}']}")

if __name__ == "__main__":
    unittest.main()


    # def test_lbs_recursive_transfer_strategy_increasing_connectivity(self):

    #     # Establish communications
    #     rec_object_min = {Object(i=7, load=0.5): 5.0}
    #     rec_object_max = {Object(i=8, load=1.0): 10.0}
    #     sent_object_min = {Object(i=9, load=0.5): 6.0}
    #     sent_object_max = {Object(i=10, load=1.0): 12.0}

    #     # Create objects
    #     obj_04 = Object(i=4, comm=ObjectCommunicator(i=4,logger=self.logger,r=rec_object_max, s=sent_object_max))
    #     obj_05 = Object(i=5, comm=ObjectCommunicator(i=5,logger=self.logger,r=rec_object_min, s=sent_object_min))
    #     obj_06 = Object(i=6, comm=None)

    #     # Define objects dict
    #     objects = {
    #       obj_04,
    #       obj_05,
    #       obj_06
    #     }

    #     # Define object list in expected order (increasing connectivity)
    #     expected_order = [
    #       obj_06,
    #       obj_05,
    #       obj_04
    #     ]

    #     self.assertEqual(
    #         self.recursive_transfer_strategy.increasing_connectivity(objects, self.rank.get_id()),
    #         expected_order
    #     )
