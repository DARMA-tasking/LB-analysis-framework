import logging
import random
import unittest
from unittest.mock import patch

from src.lbaf.Model.lbsRank import Rank
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsBlock import Block
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase
from src.lbaf.IO.lbsStatistics import compute_function_statistics
from src.lbaf.Execution.lbsCentralizedPrefixOptimizerAlgorithm import CentralizedPrefixOptimizerAlgorithm


class TestConfig(unittest.TestCase):
    def setUp(self):

        # Set up logger
        self.logger = logging.getLogger()

        # Initialize inputs
        work_model = WorkModelBase.factory(
            work_name="AffineCombination",
            parameters={},
            lgr=self.logger)
        parameters = {"do_second_stage": True}
        qoi_name = "load"

        # Create CPOA instance
        self.cpoa = CentralizedPrefixOptimizerAlgorithm(
                        work_model=work_model,
                        parameters=parameters,
                        lgr=self.logger,
                        qoi_name=qoi_name,
                        obj_qoi=qoi_name
        )

        # Set up phase
        self.sentinel_objects = {Object(i=15, load=4.5), Object(i=18, load=2.5)}
        self.migratable_objects = {Object(i=0, load=1.0), Object(i=1, load=0.5), Object(i=2, load=0.5), Object(i=3, load=0.5)}
        self.rank = Rank(r_id=0, logger=self.logger, mo=self.migratable_objects, so=self.sentinel_objects)
        self.phase = Phase(lgr=self.logger, p_id=0)
        self.phase.set_ranks([self.rank])

        # Create a shared block
        self.block = Block(b_id=0, h_id=0)
        for o in self.migratable_objects:
            o.set_shared_block(self.block)

        # Create dict of phase(s)
        self.phases = {self.phase.get_id(): self.phase}

        # Set up distributions
        self.distributions = {}

        # Set up statistics
        l_stats = compute_function_statistics(
            self.phase.get_ranks(),
            lambda x: x.get_load())
        self.statistics = {"average load": l_stats.get_average()}

    def test_lbs_cpoa_execute(self):
        self.cpoa.execute(
            self.phase.get_id(),
            self.phases,
            self.distributions,
            self.statistics,
            1
        )
        new_phase = self.cpoa.get_rebalanced_phase()
        self.assertEqual(
            new_phase.get_id(),
            self.phase.get_id()
        )


if __name__ == "__main__":
    unittest.main()
