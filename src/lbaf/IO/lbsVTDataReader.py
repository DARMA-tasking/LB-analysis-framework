import json
from logging import Logger
from multiprocessing.pool import Pool
from multiprocessing import get_context
import os
import sys

import brotli

from ..Model.lbsBlock import Block
from ..Model.lbsObject import Object
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsRank import Rank
from ..Utils.exception_handler import exc_handler


class LoadReader:
    """A class to read VT Object Map files. These json files could be compressed with Brotli.
        Each file is named as <base-name>.<node>.json, where <node> spans the number of MPI ranks that VT is utilizing.
        The schema of the compatible files is defined in <project-path>/src/IO/schemaValidator.py
    """
    
    CommCategory = {
        "SendRecv": 1,
        "CollectionToNode": 2,
        "NodeToCollection": 3,
        "Broadcast": 4,
        "CollectionToNodeBcast": 5,
        "NodeToCollectionBcast": 6,
        "CollectiveToCollectionBcast": 7,
    }

    def __init__(self, file_prefix: str, n_ranks: int, logger: Logger, file_suffix: str = "json", check_schema=True):

        # The base directory and file name for the log files
        self.__file_prefix = file_prefix

        # Data files(data loading) suffix
        self.__file_suffix = file_suffix

        # Number of ranks
        self.__n_ranks = n_ranks

        # Assign logger to instance variable
        self.__logger = logger

        # Assign schema checker
        self.__check_schema = check_schema

        # Load vt data concurrently
        self.__vt_data = {}
        with Pool(context=get_context("fork")) as pool:
            results = pool.imap_unordered(
                self._load_vt_file, range(self.__n_ranks))
            for rank, decompressed_dict in results:
                self.__vt_data[rank] = decompressed_dict

        # Perform sanity check on number of loaded phases
        l = len(next(iter(self.__vt_data.values())).get("phases"))
        if not (all(len(v.get("phases")) == l for v in self.__vt_data.values())):
            self.__logger.error(
                "Not all JSON files have the same number of phases")
            sys.excepthook = exc_handler
            raise SystemExit(1)

    def _get_rank_file_name(self, rank_id: int):
        # Convenience method also used by test harness
        return f"{self.__file_prefix}.{rank_id}.{self.__file_suffix}"

    def _load_vt_file(self, rank_id: int):
        # Assemble VT JSON file name
        file_name = self._get_rank_file_name(rank_id)
        self.__logger.info(f"Reading {file_name}")

        # Try to open, read, and decompress file
        if not os.path.isfile(file_name):
            sys.excepthook = exc_handler
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
                self.__logger.error("JSON data is missing 'type' key")
                sys.excepthook = exc_handler
                raise SystemExit(1)
        self.__logger.debug(f"{file_name} has type {schema_type}")

        # dynamically import because might be downloaded when application starts
        module = 'lbaf.imported.JSON_data_files_validator'
        if module not in sys.modules:
            from ..imported.JSON_data_files_validator import SchemaValidator # pylint:disable=C0415:import-outside-toplevel

        # Checking Schema from configuration
        if self.__check_schema:
            # Validate schema
            if SchemaValidator(
                schema_type=schema_type).is_valid(
                schema_to_validate=decompressed_dict):
                self.__logger.info(f"Valid JSON schema in {file_name}")
            else:
                self.__logger.error(f"Invalid JSON schema in {file_name}")
                SchemaValidator(
                    schema_type=schema_type).validate(
                    schema_to_validate=decompressed_dict)

        # Return rank ID and data dictionary
        return rank_id, decompressed_dict

    def _populate_rank(self, phase_id: int, rank_id: int) -> tuple:
        """ Populate rank and its communicator in phase using the JSON content."""
        # Seek phase with given ID
        phase_id_found = False
        for phase in self.__vt_data.get(rank_id).get("phases"):
            if (curr_phase_id := phase["id"]) != phase_id:
                # Ignore phases that are not of interest
                self.__logger.debug(
                    f"Ignored phase {curr_phase_id} for rank {rank_id}")
                continue
            else:
                # Desired phase was found
                phase_id_found = True
                break

        # Error out if desired phase was not found
        if not phase_id_found:
            self.__logger.error(
                f"Phase {curr_phase_id} not found for rank {rank_id}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Proceed with desired phase
        self.__logger.debug(
            f"Loading phase {curr_phase_id} for rank {rank_id}")

        # Add communications to the object
        rank_comm = {}
        communications = phase.get("communications")
        if communications:
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
                        receiver_obj_id = c_to.get("id")
                        rank_comm.setdefault(
                            receiver_obj_id, {"sent": [], "received": []})

                        # Create sender if it does not exist
                        sender_obj_id = c_from.get("id")
                        rank_comm.setdefault(
                            sender_obj_id, {"sent": [], "received": []})

                        # Create communication edges
                        rank_comm[receiver_obj_id]["received"].append(
                            {"from": c_from.get("id"),
                             "bytes": c_bytes})
                        rank_comm[sender_obj_id]["sent"].append(
                            {"to": c_to.get("id"), "bytes": c_bytes})
                        self.__logger.debug(
                            f"Added communication {num} to phase {curr_phase_id}")
                        for k, v in comm.items():
                            self.__logger.debug(f"{k}: {v}")

        # Instantiante rank for current phase
        phase_rank = Rank(self.__logger, rank_id)

        # Initialize storage for shared blocks information
        rank_blocks, task_user_defined = {}, {}

        # Iterate over tasks
        for task in phase.get("tasks", []):
            # Retrieve required values
            task_entity = task.get("entity")
            task_id = task_entity.get("id")
            task_load = task.get("time")
            task_user_defined = task.get("user_defined", {})
            subphases = task.get("subphases")

            # Instantiate object with retrieved parameters
            o = Object(
                task_id,
                r_id=rank_id,
                load=task_load,
                user_defined=task_user_defined,
                subphases=subphases)

            # Update shared block information as needed
            if (shared_id := task_user_defined.get("shared_id", -1)) > -1:
                # Create or update (memory, objects) for shared block
                rank_blocks.setdefault(
                    shared_id,
                    (task_user_defined.get("shared_bytes", 0.0), set([])))
                rank_blocks[shared_id][1].add(o)

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

    def populate_phase(self, phase_id: int) -> list:
        """ Populate phase using the JSON content."""
        # Create storage for ranks
        ranks = [None] * self.__n_ranks
        communications = {}

        # Iterate over all ranks
        for rank_id in range(self.__n_ranks):
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
        return ranks
