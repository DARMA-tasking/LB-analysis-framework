import json
from logging import Logger
from multiprocessing import Pool
import os
import sys

import brotli

from ..imported.JSON_data_files_validator import SchemaValidator
from ..Model.lbsObject import Object
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsRank import Rank
from ..Utils.exception_handler import exc_handler


class LoadReader:
    """ A class to read VT Object Map files. These json files could be compressed with Brotli.
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

        # Check schema
        self.__check_schema = check_schema

        self.vt_files = self._load_vt_files()

    def _load_vt_file(self, rank: int):
        file_name = self._get_node_trace_file_name(node_id=rank)
        self.__logger.info(f"Reading {file_name} VT object map")
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

        # Extracting type from JSON data
        schema_type = decompressed_dict.get("type")
        if schema_type is None:
            sys.excepthook = exc_handler
            raise TypeError("JSON data is missing 'type' key")
        # Checking Schema from configuration
        if self.__check_schema:
            # Validate schema
            if SchemaValidator(schema_type=schema_type).is_valid(schema_to_validate=decompressed_dict):
                self.__logger.info(f"Valid JSON schema in {file_name}")
            else:
                self.__logger.error(f"Invalid JSON schema in {file_name}")
                SchemaValidator(schema_type=schema_type).validate(schema_to_validate=decompressed_dict)
        # Print more information when requested
        self.__logger.debug(f"Finished reading file: {file_name}")

        return rank, decompressed_dict

    def _load_vt_files(self) -> dict:
        """ Load VT files into dict. """
        vt_files = {}
        with Pool() as pool:
            results = pool.imap_unordered(self._load_vt_file, range(self.__n_ranks))
            for rank, decompressed_dict in results:
                vt_files[rank] = decompressed_dict
        return vt_files

    def _get_node_trace_file_name(self, node_id):
        """ Build the file name for a given rank/node ID
        """
        return f"{self.__file_prefix}.{node_id}.{self.__file_suffix}"

    def read(self, node_id: int, phase_id: int = -1, comm: bool = False) -> tuple:
        """ Read the file for a given node/rank. If phase_id==-1 then all
            steps are read from the file; otherwise, only `phase_id` is.
        """

        # Retrieve communications from JSON reader
        iter_map = {}
        iter_map, comm = self.json_reader(
            returned_dict=iter_map,
            phase_id=phase_id,
            node_id=node_id)

        # Return map of populated ranks per iteration
        return iter_map, comm

    def read_iteration(self, phase_id: int) -> list:
        """ Read all the data in the range of ranks [0..n_p] for a given iteration `phase_id`.
            Collapse the iter_map dictionary from `read()` into a list of ranks to be returned for the given iteration.
        """

        # Create storage for ranks
        rank_list = [None] * self.__n_ranks
        communications = {}

        # Iterate over all ranks
        for p in range(self.__n_ranks):
            # Read data for given iteration and assign it to rank
            rank_iter_map, rank_comm = self.read(p, phase_id)

            # Try to retrieve rank information at given time-step
            try:
                rank_list[p] = rank_iter_map[phase_id]
            except KeyError as e:
                msg_err = f"Could not retrieve information for rank {p} at time_step {phase_id}. KeyError {e}"
                self.__logger.error(msg_err)
                sys.excepthook = exc_handler
                raise KeyError(msg_err)

            # Merge rank communication with existing ones
            if rank_comm.get(phase_id) is not None:
                for k, v in rank_comm[phase_id].items():
                    if k in communications:
                        c = communications[k]
                        c.get("sent").extend(v.get("sent"))
                        c.get("received").extend(v.get("received"))
                    else:
                        communications[k] = v

        # Build dictionary of rank objects
        rank_objects_set = set()
        for rank in rank_list:
            rank_objects_set.update(rank.get_objects())
        rank_objects_dict = {obj.get_id(): obj for obj in rank_objects_set}

        # Iterate over ranks
        for rank in rank_list:
            # Iterate over objects in rank
            for rank_obj in rank.get_objects():
                obj_id = rank_obj.get_id()
                # Check if there is any communication for the object
                obj_comm = communications.get(obj_id)
                if obj_comm:
                    sent = {rank_objects_dict.get(c.get("to")): c.get("bytes") for c in obj_comm.get("sent")
                            if rank_objects_dict.get(c.get("to"))}
                    received = {rank_objects_dict.get(c.get("from")): c.get("bytes") for c in obj_comm.get("received")
                                if rank_objects_dict.get(c.get("from"))}
                    rank_obj.set_communicator(ObjectCommunicator(i=obj_id, logger=self.__logger, r=received, s=sent))

        # Return populated list of ranks
        return rank_list

    def json_reader(self, returned_dict: dict, phase_id: int, node_id: int) -> tuple:
        """ Reader compatible with current VT Object Map files (json)
        """

        # Define phases from file
        phases = self.vt_files.get(node_id).get("phases")
        comm_dict = {}

        # Handle empty Rank case
        if not phases:
            returned_dict.setdefault(0, Rank(node_id, self.__logger))

        # Iterate over phases
        for p in phases:
            # Retrieve phase ID
            curr_phase_id = p["id"]

            # Create communicator dictionary
            comm_dict[curr_phase_id] = {}

            # Add communications to the object
            communications = p.get("communications")
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
                            comm_dict[curr_phase_id].setdefault(
                                receiver_obj_id, {"sent": [], "received": []})

                            # Create sender if it does not exist
                            sender_obj_id = c_from.get("id")
                            comm_dict[curr_phase_id].setdefault(
                                sender_obj_id, {"sent": [], "received": []})

                            # Create communication edges
                            comm_dict[curr_phase_id][receiver_obj_id]["received"].append(
                                {"from": c_from.get("id"),
                                                                                     "bytes": c_bytes})
                            comm_dict[curr_phase_id][sender_obj_id]["sent"].append(
                                {"to": c_to.get("id"), "bytes": c_bytes})
                            self.__logger.debug(
                                f"Added communication {num} to phase {curr_phase_id}")
                            for k, v in comm.items():
                                self.__logger.debug(f"{k}: {v}")

            # Iterate over tasks
            for task in p["tasks"]:
                task_time = task.get("time")
                entity = task.get("entity")
                task_object_id = entity.get("id")
                task_used_defined = task.get("user_defined")
                subphases = task.get("subphases")

                # Update rank if iteration was requested
                if phase_id in (curr_phase_id, -1):
                    # Instantiate object with retrieved parameters
                    obj = Object(
                        task_object_id,
                        task_time,
                        node_id,
                        user_defined=task_used_defined,
                        subphases=subphases)

                    # If this iteration was never encountered initialize rank object
                    returned_dict.setdefault(
                        curr_phase_id,
                        Rank(node_id, logger=self.__logger))

                    # Add object to rank given its type
                    if entity.get("migratable"):
                        returned_dict[curr_phase_id].add_migratable_object(obj)
                    else:
                        returned_dict[curr_phase_id].add_sentinel_object(obj)

                    # Print debug information when requested
                    self.__logger.debug(
                        f"Added object {task_object_id}, time = {task_time} to phase {curr_phase_id}")

        return returned_dict, comm_dict
