#
#@HEADER
###############################################################################
#
#                              lbsVTDataReader.py
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
import json
import os
import re
from logging import Logger
from multiprocessing import get_context, Manager
from multiprocessing.pool import Pool
from typing import List, Tuple

import brotli

from ..Model.lbsBlock import Block
from ..Model.lbsObject import Object
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsRank import Rank

class LoadReader:
    """A class to read VT Object Map files. These json files could be compressed with Brotli.

    Each file is named as <base-name>.<node>.json, where <node> spans the number of MPI ranks that VT is utilizing.
    The schema of the compatible files is defined in <project-path>/src/IO/schemaValidator.py
    """

    SCHEMA_VALIDATOR_CLASS = None

    CommCategory = {
        "SendRecv": 1,
        "CollectionToNode": 2,
        "NodeToCollection": 3,
        "Broadcast": 4,
        "CollectionToNodeBcast": 5,
        "NodeToCollectionBcast": 6,
        "CollectiveToCollectionBcast": 7,
    }

    def __init__(
        self, file_prefix: str, logger: Logger, file_suffix: str = "json", check_schema=True, expected_ranks=None):
        # The base directory and file name for the log files
        self.__file_prefix = file_prefix

        # Data files(data loading) suffix
        self.__file_suffix = file_suffix

        # Assign logger to instance variable
        self.__logger = logger

        # Assign the expected ranks to get
        self.expected_ranks = expected_ranks

        # Assign schema checker
        self.__check_schema = check_schema

        # Save initial communications array from every rank
        self.__communications_dict = {}

        # Save metadata dict
        manager = Manager()
        self.__metadata = manager.dict()

        # imported JSON_data_files_validator module (lazy import)
        if LoadReader.SCHEMA_VALIDATOR_CLASS is None:
            # pylint:disable=import-outside-toplevel
            from ..imported.JSON_data_files_validator import \
                SchemaValidator as \
                sv
            LoadReader.SCHEMA_VALIDATOR_CLASS = sv

        # determine the number of ranks
        self.n_ranks = self._get_n_ranks()
        self.__logger.info(f"Number of ranks: {self.n_ranks}")

        # warn user if expected_ranks is set and is different from n_ranks
        if self.expected_ranks is not None and self.expected_ranks != self.n_ranks:
            self.__logger.warn(f"Unexpected number of ranks ({self.expected_ranks} was expected)")

        # init vt data
        self.__vt_data = {}

        if self.n_ranks > 0:
            # Load vt data concurrently from rank 1 to n_ranks
            with Pool(context=get_context("fork")) as pool:
                results = pool.imap_unordered(
                    self._load_vt_file, range(0, self.n_ranks))
                for rank, decompressed_dict in results:
                    self.__vt_data[rank] = decompressed_dict

        # Perform sanity check on number of loaded phases
        l = len(next(iter(self.__vt_data.values())).get("phases"))
        if not all(len(v.get("phases")) == l for v in self.__vt_data.values()):
            self.__logger.error(
                "Not all JSON files have the same number of phases")
            raise SystemExit(1)

    def _get_n_ranks(self):
        """Determine the number of ranks automatically.

        This use the first applicable method in the following methods:
        List all data file names matching {file_prefix}.{rank_id}.{file_suffix} pattern and return max(rank_id) + 1.
        """

        # or default detect data files with pattern
        data_dir = f"{os.sep}".join(self.__file_prefix.split(os.sep)[:-1])
        pattern = re.compile(rf"^{self.__file_prefix}.(\d+).{self.__file_suffix}$")
        highest_rank = 0
        for name in os.listdir(data_dir):
            path = os.path.join(data_dir, name)
            match_result = pattern.search(path)
            if match_result:
                rank_id = int(match_result.group(1))
                highest_rank = max(highest_rank, rank_id)
        return highest_rank + 1

    def _get_rank_file_name(self, rank_id: int):
        # Convenience method also used by test harness
        return f"{self.__file_prefix}.{rank_id}.{self.__file_suffix}"

    def _load_vt_file(self, rank_id: int):
        # Assemble VT JSON file name
        file_name = self._get_rank_file_name(rank_id)
        self.__logger.info(f"Reading {file_name}")

        # Try to open, read, and decompress file
        if not os.path.isfile(file_name):
            raise FileNotFoundError(f"File {file_name} not found")
        with open(file_name, "rb") as compr_json_file:
            compr_bytes = compr_json_file.read()
            try:
                decompr_bytes = brotli.decompress(compr_bytes)
                decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
            except brotli.error:
                decompressed_dict = json.loads(compr_bytes.decode("utf-8"))

        # Determine data type
        metadata = decompressed_dict.get("metadata")
        if not metadata or not (schema_type := metadata.get("type")):
            if not (schema_type := decompressed_dict.get("type")):
                self.__logger.error(
                    "JSON data is missing 'type' key")
                raise SystemExit(1)
        self.__logger.debug(f"{file_name} has type {schema_type}")

        # Save metadata
        self.__metadata[rank_id] = metadata

        # Checking Schema from configuration
        if self.__check_schema:
            # Validate schema
            if LoadReader.SCHEMA_VALIDATOR_CLASS(    # pylint:disable=E1102:not-callable
                schema_type=schema_type).is_valid(
                schema_to_validate=decompressed_dict):
                self.__logger.info(f"Valid JSON schema in {file_name}")
            else:
                self.__logger.error(f"Invalid JSON schema in {file_name}")
                LoadReader.SCHEMA_VALIDATOR_CLASS(   # pylint:disable=E1102:not-callable
                    schema_type=schema_type).validate(
                    schema_to_validate=decompressed_dict)

        # Return rank ID and data dictionary
        return rank_id, decompressed_dict

    def _populate_rank(self, phase_id: int, rank_id: int) -> Tuple[Rank,dict]:
        """ Populate rank and its communicator in phase using the JSON content."""

        # Seek phase with given ID
        phase_id_found = False
        for phase in self.__vt_data.get(rank_id).get("phases"):
            if (curr_phase_id := phase["id"]) != phase_id:
                # Ignore phases that are not of interest
                self.__logger.debug(
                    f"Ignored phase {curr_phase_id} for rank {rank_id}")
                continue
            # Desired phase was found
            phase_id_found = True
            break

        # Error out if desired phase was not found
        if not phase_id_found:
            self.__logger.error(
                f"Phase {phase_id} not found for rank {rank_id}")
            raise SystemExit(1)

        # Proceed with desired phase
        self.__logger.debug(
            f"Loading phase {curr_phase_id} for rank {rank_id}")

        # Add communications to the object
        rank_comm = {}
        if (communications := phase.get("communications")):
            if phase_id in self.__communications_dict:
                self.__communications_dict[phase_id][rank_id] = communications
            else:
                self.__communications_dict[phase_id] = {rank_id: communications}
            for num, comm in enumerate(communications):
                # Retrieve communication attributes
                c_type = comm.get("type")
                c_to = comm.get("to")
                c_from = comm.get("from")
                c_bytes = comm.get("bytes")

                # Supports only SendRecv communication type
                if c_type == "SendRecv":
                    # Check whether both are objects
                    if c_to.get("type") == "object" and c_from.get("type") == "object":
                        # Create receiver if it does not exist
                        receiver_obj_id = c_to.get("id", c_to.get("seq_id"))
                        rank_comm.setdefault(
                            receiver_obj_id, {"sent": [], "received": []})

                        # Create sender if it does not exist
                        sender_obj_id = c_from.get("id", c_from.get("seq_id"))
                        rank_comm.setdefault(
                            sender_obj_id, {"sent": [], "received": []})

                        # Create communication edges
                        rank_comm[receiver_obj_id]["received"].append(
                            {"from": sender_obj_id,
                             "bytes": c_bytes})
                        rank_comm[sender_obj_id]["sent"].append(
                            {"to": receiver_obj_id, "bytes": c_bytes})
                        self.__logger.debug(
                            f"Added communication {num} to phase {curr_phase_id}")
                        for k, v in comm.items():
                            self.__logger.debug(f"{k}: {v}")
        else:
            self.__communications_dict.setdefault(phase_id, {rank_id: {}})

        # Instantiante rank for current phase
        phase_rank = Rank(self.__logger, rank_id)
        phase_rank.set_metadata(self.__metadata[rank_id])

        # Initialize storage for shared blocks information
        rank_blocks, task_user_defined = {}, {}

        # Iterate over tasks
        for task in phase.get("tasks", []): # pylint:disable=W0631:undefined-loop-variable
            # Retrieve required values
            task_entity = task.get("entity")
            task_id = task_entity.get("id", None)
            task_seq_id = task_entity.get("seq_id", None)
            task_load = task.get("time")
            task_user_defined = task.get("user_defined", {})
            subphases = task.get("subphases")
            collection_id = task_entity.get("collection_id")
            objgroup_id  = task_entity.get("objgroup_id")
            index = task_entity.get("index")

            # Instantiate object with retrieved parameters
            o = Object(
                seq_id=task_seq_id,
                packed_id=task_id,
                r_id=rank_id,
                load=task_load,
                user_defined=task_user_defined,
                subphases=subphases,
                collection_id=collection_id,
                index=index)

            # Update shared block information as needed
            if (shared_id := task_user_defined.get("shared_id", -1)) > -1:
                # Create or update (memory, objects) for shared block
                rank_blocks.setdefault(
                    shared_id,
                    (task_user_defined.get("shared_bytes", 0.0), set([])))
                rank_blocks[shared_id][1].add(o)

            # Add dict of currently unused parameters
            unused_params = {}
            if objgroup_id is not None:
                unused_params["objgroup_id"] = objgroup_id
            o.set_unused_params(unused_params)

            # Add object to rank given its type
            if task_entity.get("migratable"):
                phase_rank.add_migratable_object(o)
            else:
                phase_rank.add_sentinel_object(o)

            # Print debug information when requested
            self.__logger.debug(
                f"Added object {task_id}, load: {task_load} to phase {curr_phase_id}")

        # Set rank-level memory quantities of interest
        phase_rank.set_size(
            task_user_defined.get("rank_working_bytes", 0.0))
        shared_blocks = set()
        for b_id, (b_size, objects) in rank_blocks.items():
            # Create and add new block
            shared_blocks.add(block := Block(
                b_id, h_id=rank_id, size=b_size,
                o_ids={o.get_id() for o in objects}))

            # Assign block to objects attached to it
            for o in objects:
                o.set_shared_block(block)
        phase_rank.set_shared_blocks(shared_blocks)

        # Returned rank and communicators per phase
        return phase_rank, rank_comm

    def populate_phase(self, phase_id: int) -> List[Rank]:
        """ Populate phase using the JSON content."""

        # Create storage for ranks
        ranks: List[Rank] = [None] * self.n_ranks
        communications = {}

        # Iterate over all ranks
        for rank_id in range(self.n_ranks):
            # Read data for given phase and assign it to rank
            ranks[rank_id], rank_comm = self._populate_rank(phase_id, rank_id)

            # Merge rank communication with existing ones
            for k, v in rank_comm.items():
                if k in communications:
                    c = communications[k]
                    c.get("sent").extend(v.get("sent"))
                    c.get("received").extend(v.get("received"))
                else:
                    communications[k] = v

        # Build dictionary of rank objects
        rank_objects_set = set()
        for rank in ranks:
            rank_objects_set.update(rank.get_objects())
        rank_objects_dict = {obj.get_id(): obj for obj in rank_objects_set}

        # Iterate over ranks
        for r in ranks:
            # Iterate over objects in rank
            for o in r.get_objects():
                obj_id = o.get_id()
                # Check if there is any communication for the object
                obj_comm = communications.get(obj_id)
                if obj_comm:
                    sent = {
                        rank_objects_dict.get(c.get("to")): c.get("bytes")
                        for c in obj_comm.get("sent")
                        if rank_objects_dict.get(c.get("to"))}
                    received = {
                        rank_objects_dict.get(c.get("from")): c.get("bytes")
                        for c in obj_comm.get("received")
                        if rank_objects_dict.get(c.get("from"))}
                    o.set_communicator(
                        ObjectCommunicator(
                            i=obj_id, logger=self.__logger, r=received, s=sent))

        # Return populated list of ranks
        return ranks, self.__communications_dict[phase_id]
