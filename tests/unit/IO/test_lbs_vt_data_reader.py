#
#@HEADER
###############################################################################
#
#                          test_lbs_vt_data_reader.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
import os
import logging
import unittest
import subprocess

from schema import SchemaError

from src.lbaf.IO.lbsVTDataReader import LoadReader
from src.lbaf.Model.lbsObject import Object
from src.lbaf.Model.lbsObjectCommunicator import ObjectCommunicator
from src.lbaf.Model.lbsRank import Rank


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.dirname(__file__))
        self.config_dir = os.path.join(self.test_dir, "config")
        self.data_dir = os.path.join(self.test_dir, "data")
        self.file_prefix = os.path.join(self.data_dir, "synthetic-blocks", "synthetic-dataset-blocks")
        self.file_suffix = "json"
        self.logger = logging.getLogger()
        self.lr = LoadReader(file_prefix=self.file_prefix, logger=self.logger, file_suffix=self.file_suffix)
        self.rank_comm = [
            {
                5: {"sent": [], "received": [{"from": 0, "bytes": 2.0}]},
                0: {"sent": [{"to": 5, "bytes": 2.0}], "received": []},
                4: {"sent": [], "received": [{"from": 1, "bytes": 1.0}]},
                1: {"sent": [{"to": 4, "bytes": 1.0}], "received": []},
                2: {"sent": [], "received": [{"from": 3, "bytes": 1.0}]},
                3: {"sent": [{"to": 2, "bytes": 1.0}, {"to": 8, "bytes": 0.5}], "received": []},
                8: {"sent": [], "received": [{"from": 3, "bytes": 0.5}]}},
            {
                1: {"sent": [], "received": [{"from": 4, "bytes": 2.0}]},
                4: {"sent": [{"to": 1, "bytes": 2.0}], "received": []},
                8: {"sent": [], "received": [{"from": 5, "bytes": 2.0}]},
                5: {"sent": [{"to": 8, "bytes": 2.0}], "received": []},
                6: {"sent": [], "received": [{"from": 7, "bytes": 1.0}]},
                7: {"sent": [{"to": 6, "bytes": 1.0}], "received": []}},
            {
                6: {"sent": [], "received": [{"from": 8, "bytes": 1.5}]},
                8: {"sent": [{"to": 6, "bytes": 1.5}], "received": []}},
            {}
        ]
        self.ranks_iter_map = [
            {0: Rank(r_id=0, migratable_objects={Object(seq_id=3, load=0.5), Object(seq_id=2, load=0.5), Object(seq_id=0, load=1.0),
                                                 Object(seq_id=1, load=0.5)}, logger=self.logger)},
                               {0: Rank(r_id=1, migratable_objects={Object(seq_id=5, load=2.0), Object(seq_id=7, load=0.5), Object(seq_id=6, load=1.0),
                                                 Object(seq_id=4, load=0.5)}, logger=self.logger)},
                               {0: Rank(r_id=2, migratable_objects={Object(seq_id=8, load=1.5)}, logger=self.logger)},
                               {0: Rank(r_id=3, logger=self.logger)}]

        self.rank_list = [
            Rank(r_id=0, logger=self.logger,
                 migratable_objects={Object(
                     seq_id=3, load=0.5, r_id=0,
                     comm=ObjectCommunicator(i=3, logger=self.logger, s={Object(seq_id=2, load=0.5): 1.0, Object(seq_id=8, load=1.5): 0.5})),
                     Object(
                         seq_id=2, load=0.5, r_id=0,
                         comm=ObjectCommunicator(i=2, logger=self.logger, r={Object(seq_id=3, load=0.5): 1.0})),
                     Object(
                         seq_id=0, load=1.0, r_id=0,
                         comm=ObjectCommunicator(i=0, logger=self.logger, s={Object(seq_id=5, load=2.0): 2.0})),
                     Object(
                         seq_id=1, load=0.5, r_id=0,
                         comm=ObjectCommunicator(i=1, logger=self.logger, r={Object(seq_id=4, load=0.5): 2.0}, s={Object(seq_id=4, load=0.5): 1.0}))}),
            Rank(r_id=1, logger=self.logger,
                 migratable_objects={Object(
                     seq_id=5, load=2.0, r_id=1,
                     comm=ObjectCommunicator(i=5, logger=self.logger, r={Object(seq_id=0, load=1.0): 2.0}, s={Object(seq_id=8, load=1.5): 2.0})),
                     Object(
                         seq_id=7, load=0.5, r_id=1,
                         comm=ObjectCommunicator(i=7, logger=self.logger, s={Object(seq_id=6, load=1.0): 1.0})),
                     Object(
                         seq_id=6, load=1.0, r_id=1,
                         comm=ObjectCommunicator(i=6, logger=self.logger, r={Object(seq_id=7, load=0.5): 1.0, Object(seq_id=8, load=1.5): 1.5})),
                     Object(
                         seq_id=4, load=0.5, r_id=1,
                         comm=ObjectCommunicator(i=4, logger=self.logger, r={Object(seq_id=1, load=0.5): 1.0}, s={Object(seq_id=1, load=0.5): 2.0}))}),
            Rank(r_id=2, logger=self.logger,
                 migratable_objects={Object(
                     seq_id=8, load=1.5, r_id=2,
                     comm=ObjectCommunicator(i=8, logger=self.logger, r={Object(seq_id=3, load=0.5): 0.5, Object(seq_id=5, load=2.0): 2.0}, s={Object(seq_id=6, load=1.0): 1.5}))}),
            Rank(r_id=3, logger=self.logger)]

    def test_lbs_vt_data_reader_initialization(self):
        self.assertEqual(self.lr._LoadReader__file_prefix, self.file_prefix)
        self.assertEqual(self.lr._LoadReader__file_suffix, self.file_suffix)

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
            file_prefix=file_prefix, logger=self.logger, file_suffix=self.file_suffix)
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
                logger=self.logger, file_suffix=self.file_suffix)._populate_rank(0, 0)
        self.assertIn(err.exception.args[0], [
            f"File {self.file_prefix}xd.0.{self.file_suffix} not found", f"File {self.file_prefix}xd.1.{self.file_suffix} not found",
            f"File {self.file_prefix}xd.2.{self.file_suffix} not found", f"File {self.file_prefix}xd.3.{self.file_suffix} not found"
        ])

    def test_lbs_vt_data_reader_read_wrong_schema(self):
        file_prefix = os.path.join(self.data_dir, "synthetic_lb_data_wrong_schema", "data")
        with self.assertRaises(SchemaError) as err:
            LoadReader(
                file_prefix=file_prefix,
                logger=self.logger, file_suffix=self.file_suffix)._populate_rank(0, 0)

        self.assertRegex(err.exception.args[0], r"Key 'phases' error:\n(.*)\nMissing key: 'tasks'")

    def test_lbs_vt_data_reader_populate_phase(self):
        rank_list, comm_dict = self.lr.populate_phase(0)
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
                for key, value in obj.get_communicator().get_received().items():
                    prep_comm_rcv_list.append(value)
                    prep_comm_rcv_load_list.append(key.get_load())
                    prep_comm_rcv_id_list.append(key.get_id())

            for obj in generated_list:
                for key, value in obj.get_communicator().get_received().items():
                    gen_comm_rcv_list.append(value)
                    gen_comm_rcv_load_list.append(key.get_load())
                    gen_comm_rcv_id_list.append(key.get_id())

            self.assertEqual(prep_load_list, gen_load_list)
            self.assertEqual(prep_id_list, gen_id_list)
            self.assertEqual(prep_rank_list, gen_rank_list)
            self.assertEqual(prep_comm_idx_list, gen_comm_idx_list)
            self.assertEqual(prep_comm_rcv_list, gen_comm_rcv_list)
            self.assertEqual(prep_comm_rcv_load_list, gen_comm_rcv_load_list)
            self.assertEqual(prep_comm_rcv_id_list, gen_comm_rcv_id_list)

    def test_lbs_vt_data_reader_missing_communications(self):
        # run LBAF with no communications
        config_file = os.path.join(self.config_dir, "user-defined-memory-toy-problem.yaml")
        proc = subprocess.run(["python", "src/lbaf", "-c", config_file], check=True)
        self.assertEqual(0, proc.returncode)

if __name__ == "__main__":
    unittest.main()
