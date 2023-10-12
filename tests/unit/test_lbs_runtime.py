import os
import logging
import unittest

from src.lbaf.Execution.lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm
from src.lbaf.Model.lbsWorkModelBase import WorkModelBase
from src.lbaf.Execution.lbsRuntime import Runtime
from src.lbaf import PROJECT_PATH
from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsPhase import Phase
from src.lbaf.Model.lbsAffineCombinationWorkModel import AffineCombinationWorkModel
from src.lbaf.IO.lbsStatistics import compute_min_max_arrangements_work


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.logger = logging.getLogger()
        self.file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_compressed", "data")
        self.reader = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix="json")
        self.phase = Phase(self.logger, 0, reader=self.reader)

        # Initialize inputs to Runtime class
        self.phases={}
        phase = Phase(
            self.logger, 0, reader=self.reader)
        phase.populate_from_log(0)
        self.phases[0] = phase
        self.work_model = {
            "name": "AffineCombination",
        }
        self.algorithm = {
            "name": "InformAndTransfer",
            "parameters": {
                "n_iterations": 8,
                "n_rounds": 4,
                "fanout": 4,
                "order_strategy": "element_id",
                "transfer_strategy": "Recursive",
                "criterion": "Tempered",
                "max_objects_per_transfer": 8,
                "deterministic_transfer": True
            }
        }
        objects = phase.get_objects()
        alpha = 0.0
        beta = 1.0
        gamma = 0.0
        n_ranks = 4
        self.arrangements = compute_min_max_arrangements_work(objects, alpha, beta, gamma,
                                                              n_ranks, logger=self.logger)[2]
        self.rank_qoi = None
        self.object_qoi = None
        # Initialize the Runtime instances
        self.runtime = Runtime(self.phases, self.work_model, self.algorithm, self.arrangements, self.logger, self.rank_qoi, self.object_qoi)

    def test_lbs_runtime_get_work_model(self):
        self.assertEqual(self.runtime.get_work_model().__class__, AffineCombinationWorkModel)

    def test_lbs_runtime_no_phases(self):
        with self.assertRaises(SystemExit) as context:
            runtime = Runtime(None, self.work_model, self.algorithm, self.arrangements, self.logger, self.rank_qoi, self.object_qoi)
        self.assertEqual(context.exception.code, 1)

    # def test_lbs_runtime_no_algorithm(self):
    #     with self.assertRaises(SystemExit) as context:
    #         runtime = Runtime(self.phases, self.work_model, None, self.arrangements, self.logger, self.rank_qoi, self.object_qoi)
    #     self.assertEqual(context.exception.code, 1)

    def test_lbs_runtime_get_distributions(self):
        assert isinstance(self.runtime.get_distributions(), dict)

    def test_lbs_runtime_get_statistics(self):
        # Testing lbsStats in a separate unit test; just make sure it returns a dict
        assert isinstance(self.runtime.get_statistics(), dict)

    def test_lbs_runtime_execute(self):
        # Ensure execute method works as expected
        p_id = 0  # Provide a valid phase ID
        rebalanced_phase = self.runtime.execute(p_id)
        # Add assertions to check if the execute method behaves as expected
        assert rebalanced_phase is not None

if __name__ == "__main__":
    unittest.main()
