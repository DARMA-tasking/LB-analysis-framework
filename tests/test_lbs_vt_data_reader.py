import os
import sys
try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-2])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    sys.exit(1)

import logging
import unittest

from schema import SchemaError

from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsObjectCommunicator import ObjectCommunicator
from src.lbaf.Model.lbsRank import Rank


class TestConfig(unittest.TestCase):
    def setUp(self):
        try:
            self.data_dir = os.path.join(f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-1]), 'data')
            sys.path.append(self.data_dir)
        except Exception as e:
            print(f"Can not add data path to system path! Exiting!\nERROR: {e}")
            sys.exit(1)
        self.file_prefix = os.path.join(self.data_dir, 'synthetic_lb_data', 'data')
        self.logger = logging.getLogger()
        self.lr = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix='json')
        self.ranks_comm = [
            {0: {
                5: {'sent': [], 'received': [{'from': 0, 'bytes': 2.0}]},
                0: {'sent': [{'to': 5, 'bytes': 2.0}], 'received': []},
                4: {'sent': [], 'received': [{'from': 1, 'bytes': 1.0}]},
                1: {'sent': [{'to': 4, 'bytes': 1.0}], 'received': []},
                2: {'sent': [], 'received': [{'from': 3, 'bytes': 1.0}]},
                3: {'sent': [{'to': 2, 'bytes': 1.0}, {'to': 8, 'bytes': 0.5}], 'received': []},
                8: {'sent': [], 'received': [{'from': 3, 'bytes': 0.5}]}}},
            {0: {
                1: {'sent': [], 'received': [{'from': 4, 'bytes': 2.0}]},
                4: {'sent': [{'to': 1, 'bytes': 2.0}], 'received': []},
                8: {'sent': [], 'received': [{'from': 5, 'bytes': 2.0}]},
                5: {'sent': [{'to': 8, 'bytes': 2.0}], 'received': []},
                6: {'sent': [], 'received': [{'from': 7, 'bytes': 1.0}]},
                7: {'sent': [{'to': 6, 'bytes': 1.0}], 'received': []}}},
            {0: {
                6: {'sent': [], 'received': [{'from': 8, 'bytes': 1.5}]},
                8: {'sent': [{'to': 6, 'bytes': 1.5}], 'received': []}}},
            {}
        ]
        self.ranks_iter_map = [{0: Rank(i=0, mo={Object(i=3, t=0.5), Object(i=2, t=0.5), Object(i=0, t=1.0),
                                                 Object(i=1, t=0.5)}, logger=self.logger)},
                               {0: Rank(i=1, mo={Object(i=5, t=2.0), Object(i=7, t=0.5), Object(i=6, t=1.0),
                                                 Object(i=4, t=0.5)}, logger=self.logger)},
                               {0: Rank(i=2, mo={Object(i=8, t=1.5)}, logger=self.logger)},
                               {0: Rank(i=3, logger=self.logger)}]

        self.rank_list = [Rank(i=0, mo={Object(i=3, t=0.5, p=0, c=ObjectCommunicator(i=3, logger=self.logger,
                                                                                     s={Object(i=2, t=0.5): 1.0,
                                                                                        Object(i=8, t=1.5): 0.5})),
                                        Object(i=2, t=0.5, p=0, c=ObjectCommunicator(i=2, logger=self.logger,
                                                                                     r={Object(i=3, t=0.5): 1.0})),
                                        Object(i=0, t=1.0, p=0, c=ObjectCommunicator(i=0, logger=self.logger,
                                                                                     s={Object(i=5, t=2.0): 2.0})),
                                        Object(i=1, t=0.5, p=0, c=ObjectCommunicator(i=1, logger=self.logger,
                                                                                     r={Object(i=4, t=0.5): 2.0},
                                                                                     s={Object(i=4, t=0.5): 1.0}))},
                               logger=self.logger),
                          Rank(i=1, mo={Object(i=5, t=2.0, p=1, c=ObjectCommunicator(i=5, logger=self.logger,
                                                                                     r={Object(i=0, t=1.0): 2.0},
                                                                                     s={Object(i=8, t=1.5): 2.0})),
                                        Object(i=7, t=0.5, p=1, c=ObjectCommunicator(i=7, logger=self.logger,
                                                                                     s={Object(i=6, t=1.0): 1.0})),
                                        Object(i=6, t=1.0, p=1, c=ObjectCommunicator(i=6, logger=self.logger,
                                                                                     r={Object(i=7, t=0.5): 1.0,
                                                                                        Object(i=8, t=1.5): 1.5})),
                                        Object(i=4, t=0.5, p=1, c=ObjectCommunicator(i=4, logger=self.logger,
                                                                                     r={Object(i=1, t=0.5): 1.0},
                                                                                     s={Object(i=1, t=0.5): 2.0}))},
                               logger=self.logger),
                          Rank(i=2, mo={Object(i=8, t=1.5, p=2, c=ObjectCommunicator(i=8, logger=self.logger,
                                                                                     r={Object(i=3, t=0.5): 0.5,
                                                                                        Object(i=5, t=2.0): 2.0},
                                                                                     s={Object(i=6, t=1.0): 1.5}))},
                               logger=self.logger),
                          Rank(i=3, logger=self.logger)]

    def test_lbs_vt_data_reader_initialization(self):
        self.assertEqual(self.lr._LoadReader__file_prefix, self.file_prefix)
        self.assertEqual(self.lr._LoadReader__file_suffix, 'json')

    def test_lbs_vt_data_reader_get_node_trace_file_name_001(self):
        file_name = f"{self.lr._LoadReader__file_prefix}.0.{self.lr._LoadReader__file_suffix}"
        self.assertEqual(file_name, self.lr.get_node_trace_file_name(node_id=0))

    def test_lbs_vt_data_reader_get_node_trace_file_name_002(self):
        file_name = f"{self.lr._LoadReader__file_prefix}.100.{self.lr._LoadReader__file_suffix}"
        self.assertEqual(file_name, self.lr.get_node_trace_file_name(node_id=100))

    def test_lbs_vt_data_reader_get_node_trace_file_name_003(self):
        # Node_id is an in 000 is converted to 0
        file_name = f"{self.lr._LoadReader__file_prefix}.000.{self.lr._LoadReader__file_suffix}"
        self.assertNotEqual(file_name, self.lr.get_node_trace_file_name(node_id=000))

    def test_lbs_vt_data_reader_read(self):
        for phase in range(4):
            rank_iter_map, rank_comm = self.lr.read(phase, 0)
            self.assertEqual(self.ranks_comm[phase], rank_comm)
            prepared_list = sorted(list(self.ranks_iter_map[phase].get(0).get_migratable_objects()),
                                   key=lambda x: x.get_id())
            generated_list = sorted(list(rank_iter_map.get(0).get_migratable_objects()), key=lambda x: x.get_id())
            prep_time_list = [obj.get_time() for obj in prepared_list]
            gen_time_list = [obj.get_time() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            self.assertEqual(prep_time_list, gen_time_list)
            self.assertEqual(prep_id_list, gen_id_list)

    def test_lbs_vt_data_reader_read_compressed(self):
        file_prefix = os.path.join(self.data_dir, 'synthetic_lb_stats_compressed', 'data')
        lr = LoadReader(file_prefix=file_prefix, logger=self.logger, file_suffix='json')
        for phase in range(4):
            rank_iter_map, rank_comm = lr.read(phase, 0)
            self.assertEqual(self.ranks_comm[phase], rank_comm)
            prepared_list = sorted(list(self.ranks_iter_map[phase].get(0).get_migratable_objects()),
                                   key=lambda x: x.get_id())
            generated_list = sorted(list(rank_iter_map.get(0).get_migratable_objects()), key=lambda x: x.get_id())
            prep_time_list = [obj.get_time() for obj in prepared_list]
            gen_time_list = [obj.get_time() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            self.assertEqual(prep_time_list, gen_time_list)
            self.assertEqual(prep_id_list, gen_id_list)

    def test_lbs_vt_data_reader_read_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as err:
            LoadReader(file_prefix=f"{self.file_prefix}xd", logger=self.logger, file_suffix='json').read(0, 0)
        self.assertEqual(err.exception.args[0], f"File {self.file_prefix}xd.0.json not found!")

    def test_lbs_vt_data_reader_read_wrong_schema(self):
        file_prefix = os.path.join(self.data_dir, 'synthetic_lb_stats_wrong_schema', 'data')
        with self.assertRaises(SchemaError) as err:
            LoadReader(file_prefix=file_prefix, logger=self.logger, file_suffix='json').read(0, 0)
        with open(os.path.join(self.data_dir, 'synthetic_lb_stats_wrong_schema', 'schema_error.txt'), 'rt') as se:
            err_msg = se.read()
        self.assertEqual(err.exception.args[0], err_msg)

    def test_lbs_vt_data_reader_json_reader(self):
        for phase in range(4):
            file_name = self.lr.get_node_trace_file_name(phase)
            rank_iter_map, rank_comm = self.lr.json_reader(returned_dict={}, file_name=file_name, phase_ids=0,
                                                           node_id=phase)
            self.assertEqual(self.ranks_comm[phase], rank_comm)
            prepared_list = sorted(list(self.ranks_iter_map[phase].get(0).get_migratable_objects()),
                                   key=lambda x: x.get_id())
            generated_list = sorted(list(rank_iter_map.get(0).get_migratable_objects()), key=lambda x: x.get_id())
            prep_time_list = [obj.get_time() for obj in prepared_list]
            gen_time_list = [obj.get_time() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            self.assertEqual(prep_time_list, gen_time_list)
            self.assertEqual(prep_id_list, gen_id_list)

    def test_lbs_vt_data_reader_read_iteration(self):
        rank_list = self.lr.read_iteration(n_p=4, phase_id=0)
        for rank_real, rank_mock in zip(rank_list, self.rank_list):
            generated_list = sorted(list(rank_real.get_migratable_objects()), key=lambda x: x.get_id())
            prepared_list = sorted(list(rank_mock.get_migratable_objects()), key=lambda x: x.get_id())
            prep_time_list = [obj.get_time() for obj in prepared_list]
            gen_time_list = [obj.get_time() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            prep_rank_list = [obj.get_rank_id() for obj in prepared_list]
            gen_rank_list = [obj.get_rank_id() for obj in generated_list]

            prep_comm_idx_list = [obj.get_communicator()._ObjectCommunicator__object_index for obj in prepared_list]
            gen_comm_idx_list = [obj.get_communicator()._ObjectCommunicator__object_index for obj in generated_list]

            prep_comm_rcv_list = []
            prep_comm_rcv_time_list = []
            prep_comm_rcv_id_list = []
            gen_comm_rcv_list = []
            gen_comm_rcv_time_list = []
            gen_comm_rcv_id_list = []

            for obj in prepared_list:
                for key, val in obj.get_communicator().get_received().items():
                    prep_comm_rcv_list.append(val)
                    prep_comm_rcv_time_list.append(key.get_time())
                    prep_comm_rcv_id_list.append(key.get_id())

            for obj in generated_list:
                for key, val in obj.get_communicator().get_received().items():
                    gen_comm_rcv_list.append(val)
                    gen_comm_rcv_time_list.append(key.get_time())
                    gen_comm_rcv_id_list.append(key.get_id())

            self.assertEqual(prep_time_list, gen_time_list)
            self.assertEqual(prep_id_list, gen_id_list)
            self.assertEqual(prep_rank_list, gen_rank_list)
            self.assertEqual(prep_comm_idx_list, gen_comm_idx_list)
            self.assertEqual(prep_comm_rcv_list, gen_comm_rcv_list)
            self.assertEqual(prep_comm_rcv_time_list, gen_comm_rcv_time_list)
            self.assertEqual(prep_comm_rcv_id_list, gen_comm_rcv_id_list)

    def test_lbs_vt_data_reader_read_iteration_key_error(self):
        with self.assertRaises(KeyError) as err:
            rank_list = self.lr.read_iteration(n_p=4, phase_id=5)
            print(err.exception.args[0])
        self.assertEqual(err.exception.args[0], "Could not retrieve information for rank 0 at time_step 5. KeyError 5")


if __name__ == '__main__':
    unittest.main()
