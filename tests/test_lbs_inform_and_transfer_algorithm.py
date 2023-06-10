import logging
import random
import unittest
from unittest.mock import patch

from lbaf.Model.lbsMessage import Message
from lbaf.Model.lbsObject import Object
from lbaf.Model.lbsRank import Rank
from lbaf.Execution.lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
from lbaf.Model.lbsWorkModelBase import WorkModelBase

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
    def test_lbs_inform_and_transfer_initialize_message(self, random_mock):
        self.rank._Rank__known_loads[self.rank] = self.rank.get_load()
        temp_rank_1 = Rank(r_id=1, logger=self.logger)
        temp_rank_1._Rank__known_loads[temp_rank_1] = 4.0
        temp_rank_2 = Rank(r_id=2, logger=self.logger)
        temp_rank_2._Rank__known_loads[temp_rank_2] = 5.0
        random_mock.return_value = [temp_rank_1, temp_rank_2]
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__initialize_message(
                self.rank,
                loads={self.rank, temp_rank_1, temp_rank_2},
                f=4)[0],
            [temp_rank_1, temp_rank_2]
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__initialize_message(
                self.rank,
                loads={self.rank, temp_rank_1, temp_rank_2},
                f=4)[1].get_round(),
            Message(1, {"loads": self.rank._Rank__known_loads}).get_round()
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__initialize_message(
                self.rank,
                loads={self.rank, temp_rank_1, temp_rank_2},
                f=4)[1].get_content(),
            Message(1, {"loads": self.rank._Rank__known_loads}).get_content()
        )

    @patch.object(random, "sample")
    def test_lbs_inform_and_transfer_forward_message(self, random_mock):
        self.rank._Rank__known_loads[self.rank] = self.rank.get_load()
        temp_rank_1 = Rank(r_id=1, logger=self.logger)
        temp_rank_1._Rank__known_loads[temp_rank_1] = 4.0
        temp_rank_2 = Rank(r_id=2, logger=self.logger)
        temp_rank_2._Rank__known_loads[temp_rank_2] = 5.0
        random_mock.return_value = [temp_rank_1, temp_rank_2]
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r=self.rank,
                loads=set(),
                f=4)[0],
            [temp_rank_1, temp_rank_2]
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r=self.rank,
                loads=set(),
                f=4)[1].get_round(),
            Message(2, {"loads": self.rank._Rank__known_loads}).get_round()
        )
        self.assertEqual(
            self.inform_and_transfer._InformAndTransferAlgorithm__forward_message(
                i=2,
                r=self.rank,
                loads=set(),
                f=4)[1].get_content(),
            Message(2, {"loads": self.rank._Rank__known_loads}).get_content()
        )

    def test_lbs_inform_and_transfer_process_message(self):
        self.rank._Rank__known_loads[self.rank] = self.rank.get_load()
        temp_rank_1 = Rank(r_id=1, logger=self.logger)
        temp_rank_1._Rank__known_loads[temp_rank_1] = 4.0
        self.assertEqual(self.rank.get_load(), 9.5)
        self.inform_and_transfer._InformAndTransferAlgorithm__process_message(
            self.rank,
            Message(1, {"loads": self.rank._Rank__known_loads})
        )
        self.assertEqual(
            self.rank._Rank__known_loads,
            {self.rank: 9.5}
        )

if __name__ == "__main__":
    unittest.main()