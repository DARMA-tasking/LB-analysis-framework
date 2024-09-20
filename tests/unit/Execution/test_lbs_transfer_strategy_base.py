import logging
import unittest

from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase
from src.lbaf.Execution.lbsCriterionBase import CriterionBase
from src.lbaf.Execution.lbsTransferStrategyBase import TransferStrategyBase


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
        self.migratable_objects = {Object(seq_id=0, load=1.0), Object(seq_id=1, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=3, load=0.5)}
        self.sentinel_objects = {Object(seq_id=15, load=4.5), Object(seq_id=18, load=2.5)}
        self.rank = Rank(r_id=0, mo=self.migratable_objects, so=self.sentinel_objects, logger=self.logger)
        self.transfer_strategy=TransferStrategyBase(criterion=self.criterion, parameters={}, logger=self.logger)

    def test_lbs_transfer_strategy_base_factory_wrong_name(self):
        with self.assertRaises(SystemExit) as err:
            TransferStrategyBase.factory("Not a good name", parameters={}, criterion=self.criterion, logger=self.logger)
        self.assertEqual(err.exception.code, 1)

    def test_lbs_transfer_strategy_base_wrong_logger(self):
        with self.assertRaises(SystemExit) as err:
            transfer_base = TransferStrategyBase(criterion=self.criterion, parameters={}, logger=None)
        self.assertEqual(err.exception.code, 1)

    def test_lbs_transfer_strategy_base_wrong_criterion(self):
        with self.assertRaises(SystemExit) as err:
            transfer_base = TransferStrategyBase(criterion=None, parameters={}, logger=self.logger)
        self.assertEqual(err.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
