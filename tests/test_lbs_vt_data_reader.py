import os
import logging
import unittest

from schema import SchemaError

from lbaf import PROJECT_PATH
from lbaf.IO.lbsVTDataReader import LoadReader
from lbaf.Model.lbsObject import Object
from lbaf.Model.lbsObjectCommunicator import ObjectCommunicator
from lbaf.Model.lbsRank import Rank


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(PROJECT_PATH, "tests", "data")
        self.file_prefix = os.path.join(self.data_dir, "synthetic_lb_data", "data")
        self.logger = logging.getLogger()
        self.lr = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix="json")
        self.rank_comm = [
            {
                5: {"sent": [], "received": [{"from": 0, "bytes": 2.0}]},
                0: {"sent": [{'to': 5, "bytes": 2.0}], "received": []},
                4: {"sent": [], "received": [{"from": 1, "bytes": 1.0}]},
                1: {"sent": [{'to': 4, "bytes": 1.0}], "received": []},
                2: {"sent": [], "received": [{"from": 3, "bytes": 1.0}]},
                3: {"sent": [{'to': 2, "bytes": 1.0}, {'to': 8, "bytes": 0.5}], "received": []},
                8: {"sent": [], "received": [{"from": 3, "bytes": 0.5}]}},
            {
                1: {"sent": [], "received": [{"from": 4, "bytes": 2.0}]},
                4: {"sent": [{'to': 1, "bytes": 2.0}], "received": []},
                8: {"sent": [], "received": [{"from": 5, "bytes": 2.0}]},
                5: {"sent": [{'to': 8, "bytes": 2.0}], "received": []},
                6: {"sent": [], "received": [{"from": 7, "bytes": 1.0}]},
                7: {"sent": [{'to': 6, "bytes": 1.0}], "received": []}},
            {
                6: {"sent": [], "received": [{"from": 8, "bytes": 1.5}]},
                8: {"sent": [{'to': 6, "bytes": 1.5}], "received": []}},
            {}
        ]
        self.ranks_iter_map = [
            {0: Rank(r_id=0, mo={Object(i=3, load=0.5), Object(i=2, load=0.5), Object(i=0, load=1.0),
                                                 Object(i=1, load=0.5)}, logger=self.logger)},
                               {0: Rank(r_id=1, mo={Object(i=5, load=2.0), Object(i=7, load=0.5), Object(i=6, load=1.0),
                                                 Object(i=4, load=0.5)}, logger=self.logger)},
                               {0: Rank(r_id=2, mo={Object(i=8, load=1.5)}, logger=self.logger)},
                               {0: Rank(r_id=3, logger=self.logger)}]

        self.rank_list = [
            Rank(r_id=0, logger=self.logger,
                 mo={Object(
                     i=3, load=0.5, r_id=0,
                     comm=ObjectCommunicator(i=3, logger=self.logger, s={Object(i=2, load=0.5): 1.0, Object(i=8, load=1.5): 0.5})),
                     Object(
                         i=2, load=0.5, r_id=0,
                         comm=ObjectCommunicator(i=2, logger=self.logger, r={Object(i=3, load=0.5): 1.0})),
                     Object(
                         i=0, load=1.0, r_id=0,
                         comm=ObjectCommunicator(i=0, logger=self.logger, s={Object(i=5, load=2.0): 2.0})),
                     Object(
                         i=1, load=0.5, r_id=0,
                         comm=ObjectCommunicator(i=1, logger=self.logger, r={Object(i=4, load=0.5): 2.0}, s={Object(i=4, load=0.5): 1.0}))}),
            Rank(r_id=1, logger=self.logger,
                 mo={Object(
                     i=5, load=2.0, r_id=1,
                     comm=ObjectCommunicator(i=5, logger=self.logger, r={Object(i=0, load=1.0): 2.0}, s={Object(i=8, load=1.5): 2.0})),
                     Object(
                         i=7, load=0.5, r_id=1,
                         comm=ObjectCommunicator(i=7, logger=self.logger, s={Object(i=6, load=1.0): 1.0})),
                     Object(
                         i=6, load=1.0, r_id=1,
                         comm=ObjectCommunicator(i=6, logger=self.logger, r={Object(i=7, load=0.5): 1.0, Object(i=8, load=1.5): 1.5})),
                     Object(
                         i=4, load=0.5, r_id=1,
                         comm=ObjectCommunicator(i=4, logger=self.logger, r={Object(i=1, load=0.5): 1.0}, s={Object(i=1, load=0.5): 2.0}))}),
            Rank(r_id=2, logger=self.logger,
                 mo={Object(
                     i=8, load=1.5, r_id=2,
                     comm=ObjectCommunicator(i=8, logger=self.logger, r={Object(i=3, load=0.5): 0.5, Object(i=5, load=2.0): 2.0}, s={Object(i=6, load=1.0): 1.5}))}),
            Rank(r_id=3, logger=self.logger)]

    def test_lbs_vt_data_reader_initialization(self):
        self.assertEqual(self.lr._LoadReader__file_prefix, self.file_prefix)
        self.assertEqual(self.lr._LoadReader__file_suffix, "json")

    def test_lbs_vt_data_reader_get_rank_file_name_001(self):
        file_name = f"{self.lr._LoadReader__file_prefix}.0.{self.lr._LoadReader__file_suffix}"
        self.assertEqual(file_name, self.lr._get_rank_file_name(0))

    def test_lbs_vt_data_reader_get_rank_file_name_002(self):
        file_name = f"{self.lr._LoadReader__file_prefix}.100.{self.lr._LoadReader__file_suffix}"
        self.assertEqual(file_name, self.lr._get_rank_file_name(100))

    def test_lbs_vt_data_reader_get_rank_file_name_003(self):
        file_name = f"{self.lr._LoadReader__file_prefix}.000.{self.lr._LoadReader__file_suffix}"
        self.assertNotEqual(file_name, self.lr._get_rank_file_name(000))

    def test_lbs_vt_data_reader_populate_rank(self):
        for rank_id in range(4):
            phase_rank, rank_comm = self.lr._populate_rank(0, rank_id)
            self.assertEqual(self.rank_comm[rank_id], rank_comm)
            prepared_list = sorted(
                list(self.ranks_iter_map[rank_id].get(0).get_migratable_objects()),
                key=lambda x: x.get_id())
            generated_list = sorted(
                list(phase_rank.get_migratable_objects()),
                key=lambda x: x.get_id())
            prep_load_list = [obj.get_load() for obj in prepared_list]
            gen_load_list = [obj.get_load() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            self.assertEqual(prep_load_list, gen_load_list)
            self.assertEqual(prep_id_list, gen_id_list)

    def test_lbs_vt_data_reader_read_compressed(self):
        file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_compressed", "data")
        lr = LoadReader(
            file_prefix=file_prefix, logger=self.logger, file_suffix="json")
        for rank_id in range(4):
            phase_rank, rank_comm = lr._populate_rank(0, rank_id)
            self.assertEqual(self.rank_comm[rank_id], rank_comm)
            prepared_list = sorted(
                list(self.ranks_iter_map[rank_id].get(0).get_migratable_objects()),
                key=lambda x: x.get_id())
            generated_list = sorted(
                list(phase_rank.get_migratable_objects()),
                key=lambda x: x.get_id())
            prep_load_list = [obj.get_load() for obj in prepared_list]
            gen_load_list = [obj.get_load() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            self.assertEqual(prep_load_list, gen_load_list)
            self.assertEqual(prep_id_list, gen_id_list)

    def test_lbs_vt_data_reader_read_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as err:
            LoadReader(
                file_prefix=f"{self.file_prefix}xd",
                logger=self.logger, file_suffix="json")._populate_rank(0, 0)
        self.assertIn(err.exception.args[0], [
            f"File {self.file_prefix}xd.0.json not found", f"File {self.file_prefix}xd.1.json not found",
            f"File {self.file_prefix}xd.2.json not found", f"File {self.file_prefix}xd.3.json not found"
        ])

    def test_lbs_vt_data_reader_read_wrong_schema(self):
        file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_wrong_schema", "data")
        with self.assertRaises(SchemaError) as err:
            LoadReader(
                file_prefix=file_prefix,
                logger=self.logger, file_suffix="json")._populate_rank(0, 0)
        list_of_err_msg = []
        with open(os.path.join(
            self.data_dir,
            "synthetic_lb_data_wrong_schema", "schema_error_0.txt"), "rt") as se:
            err_msg_0 = se.read()
        list_of_err_msg.append(err_msg_0)
        with open(os.path.join(
            self.data_dir,
            "synthetic_lb_data_wrong_schema", 'schema_error_1.txt'), "rt") as se:
            err_msg_1 = se.read()
        list_of_err_msg.append(err_msg_1)
        with open(os.path.join(
            self.data_dir,
            "synthetic_lb_data_wrong_schema", 'schema_error_2.txt'), "rt") as se:
            err_msg_2 = se.read()
        list_of_err_msg.append(err_msg_2)
        with open(os.path.join(
            self.data_dir,
            "synthetic_lb_data_wrong_schema", 'schema_error_3.txt'), "rt") as se:
            err_msg_3 = se.read()
        list_of_err_msg.append(err_msg_3)
        self.assertIn(err.exception.args[0], list_of_err_msg)

    def test_lbs_vt_data_reader_populate_rank(self):
        for rank_id in range(4):
            file_name = self.lr._get_rank_file_name(rank_id)
            phase_rank, rank_comm = self.lr._populate_rank(0, rank_id)
            self.assertEqual(self.rank_comm[rank_id], rank_comm)
            prepared_list = sorted(
                list(self.ranks_iter_map[rank_id].get(0).get_migratable_objects()),
                key=lambda x: x.get_id())
            generated_list = sorted(
                list(phase_rank.get_migratable_objects()),
                key=lambda x: x.get_id())
            prep_load_list = [obj.get_load() for obj in prepared_list]
            gen_load_list = [obj.get_load() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            self.assertEqual(prep_load_list, gen_load_list)
            self.assertEqual(prep_id_list, gen_id_list)

    def test_lbs_vt_data_reader_populate_phase(self):
        rank_list = self.lr.populate_phase(0)
        for rank_real, rank_mock in zip(rank_list, self.rank_list):
            generated_list = sorted(list(rank_real.get_migratable_objects()), key=lambda x: x.get_id())
            prepared_list = sorted(list(rank_mock.get_migratable_objects()), key=lambda x: x.get_id())
            prep_load_list = [obj.get_load() for obj in prepared_list]
            gen_load_list = [obj.get_load() for obj in generated_list]
            prep_id_list = [obj.get_id() for obj in prepared_list]
            gen_id_list = [obj.get_id() for obj in generated_list]
            prep_rank_list = [obj.get_rank_id() for obj in prepared_list]
            gen_rank_list = [obj.get_rank_id() for obj in generated_list]

            prep_comm_idx_list = [obj.get_communicator()._ObjectCommunicator__object_index for obj in prepared_list]
            gen_comm_idx_list = [obj.get_communicator()._ObjectCommunicator__object_index for obj in generated_list]

            prep_comm_rcv_list = []
            prep_comm_rcv_load_list = []
            prep_comm_rcv_id_list = []
            gen_comm_rcv_list = []
            gen_comm_rcv_load_list = []
            gen_comm_rcv_id_list = []

            for obj in prepared_list:
                for key, val in obj.get_communicator().get_received().items():
                    prep_comm_rcv_list.append(val)
                    prep_comm_rcv_load_list.append(key.get_load())
                    prep_comm_rcv_id_list.append(key.get_id())

            for obj in generated_list:
                for key, val in obj.get_communicator().get_received().items():
                    gen_comm_rcv_list.append(val)
                    gen_comm_rcv_load_list.append(key.get_load())
                    gen_comm_rcv_id_list.append(key.get_id())

            self.assertEqual(prep_load_list, gen_load_list)
            self.assertEqual(prep_id_list, gen_id_list)
            self.assertEqual(prep_rank_list, gen_rank_list)
            self.assertEqual(prep_comm_idx_list, gen_comm_idx_list)
            self.assertEqual(prep_comm_rcv_list, gen_comm_rcv_list)
            self.assertEqual(prep_comm_rcv_load_list, gen_comm_rcv_load_list)
            self.assertEqual(prep_comm_rcv_id_list, gen_comm_rcv_id_list)

if __name__ == '__main__':
    unittest.main()
