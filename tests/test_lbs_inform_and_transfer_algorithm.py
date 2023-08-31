import logging
import random
import unittest
from unittest.mock import patch

from src.lbaf.Model.lbsMessage import Message
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Execution.lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()
        self.migratable_objects = {Object(i=0, load=1.0), Object(i=1, load=0.5), Object(i=2, load=0.5), Object(i=3, load=0.5)}
        self.sentinel_objects = {Object(i=15, load=4.5), Object(i=18, load=2.5)}
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
        self.inform_and_transfer = InformAndTransferAlgorithm(
            work_model=WorkModelBase(),
            parameters={
                "n_iterations": 8,
                "n_rounds": 4,
                "fanout": 4,
                "order_strategy": "element_id",
                "transfer_strategy": "Recursive",
                "criterion": "Tempered",
                "max_objects_per_transfer": 8,
                "deterministic_transfer": True
            },
            lgr=self.logger,
            rank_qoi=None,
            object_qoi=None)

    @patch.object(random, "sample")
    def test_lbs_inform_and_transfer_forward_message(self, random_mock):
        temp_rank_1 = Rank(r_id=1, logger=self.logger)
        temp_rank_2 = Rank(r_id=2, logger=self.logger)
        random_mock.return_value = [temp_rank_1, temp_rank_2]

        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r_snd=self.rank,
                f=4)[0],
            [temp_rank_1, temp_rank_2]
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r_snd=self.rank,
                f=4)[1].get_round(),
            Message(2, {"loads": self.inform_and_transfer.get_known_peers()}).get_round()
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r_snd=self.rank,
                f=4)[1].get_support(),
            Message(2, self.inform_and_transfer.get_known_peers()[self.rank]).get_support()
        )
    def test_lbs_inform_and_transfer_process_message(self):
        temp_rank_1 = Rank(r_id=1, logger=self.logger)
        self.inform_and_transfer._InformAndTransferAlgorithm__process_message(
            self.rank, Message(1,{temp_rank_1: 4.0})
        )
        known_peers = self.inform_and_transfer.get_known_peers()
        self.assertEqual(known_peers, {self.rank: {self.rank, temp_rank_1}})

if __name__ == "__main__":
    unittest.main()