import json
from logging import Logger
import os
import sys

import brotli

from .schemaValidator import SchemaValidator
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

    def __init__(self, file_prefix: str, logger: Logger, file_suffix: str = "json"):
        # The base directory and file name for the log files
        self.__file_prefix = file_prefix

        # Data files(data loading) suffix
        self.__file_suffix = file_suffix

        # Assign logger to instance variable
        self.__logger = logger

    def get_node_trace_file_name(self, node_id):
        """ Build the file name for a given rank/node ID
        """
        return f"{self.__file_prefix}.{node_id}.{self.__file_suffix}"

    def read(self, node_id: int, phase_id: int = -1, comm: bool = False) -> tuple:
        """ Read the file for a given node/rank. If phase_id==-1 then all
            steps are read from the file; otherwise, only `phase_id` is.
        """

        # Retrieve file name for given node and make sure that it exists
        file_name = self.get_node_trace_file_name(node_id)
        self.__logger.info(f"Reading {file_name} VT object map")
        if not os.path.isfile(file_name):
            sys.excepthook = exc_handler
            raise FileNotFoundError(f"File {file_name} not found!")

        # Retrieve communications from JSON reader
        iter_map = {}
        iter_map, comm = self.json_reader(
            returned_dict=iter_map,
            file_name=file_name,
            phase_ids=phase_id,
            node_id=node_id)

        # Print more information when requested
        self.__logger.debug(f"Finished reading file: {file_name}")

        # Return map of populated ranks per iteration
        return iter_map, comm

    def read_iteration(self, n_p: int, phase_id: int) -> list:
        """ Read all the data in the range of ranks [0..n_p] for a given iteration `phase_id`.
            Collapse the iter_map dictionary from `read()` into a list of ranks to be returned for the given iteration.
        """

        # Create storage for ranks
        rank_list = [None] * n_p
        communications = {}

        # Iterate over all ranks
        for p in range(n_p):
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

    def json_reader(self, returned_dict: dict, file_name: str, phase_ids, node_id: int) -> tuple:
        """ Reader compatible with current VT Object Map files (json)
        """
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

        # Validate schema
        if SchemaValidator(schema_type=schema_type).is_valid(schema_to_validate=decompressed_dict):
            self.__logger.info(f"Valid JSON schema in {file_name}")
        else:
            self.__logger.error(f"Invalid JSON schema in {file_name}")
            SchemaValidator(schema_type=schema_type).validate(schema_to_validate=decompressed_dict)

        # Define phases from file
        phases = decompressed_dict["phases"]
        comm_dict = {}

        # Handle empty Rank case
        if not phases:
            returned_dict.setdefault(0, Rank(node_id, self.__logger))

        # Iterate over phases
        for phase in phases:
            # Retrieve phase ID
            phase_id = phase["id"]

            # Create communicator dictionary
            comm_dict[phase_id] = {}

            # Add communications to the object
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
                            comm_dict[phase_id].setdefault(receiver_obj_id, {"sent": [], "received": []})

                            # Create sender if it does not exist
                            sender_obj_id = c_from.get("id")
                            comm_dict[phase_id].setdefault(sender_obj_id, {"sent": [], "received": []})

                            # Create communication edges
                            comm_dict[phase_id][receiver_obj_id]["received"].append({"from": c_from.get("id"),
                                                                                     "bytes": c_bytes})
                            comm_dict[phase_id][sender_obj_id]["sent"].append({"to": c_to.get("id"), "bytes": c_bytes})
                            self.__logger.debug(f"Added communication {num} to phase {phase_id}")
                            for k, v in comm.items():
                                self.__logger.debug(f"{k}: {v}")

            # Iterate over tasks
            for task in phase["tasks"]:
                task_time = task.get("time")
                entity = task.get("entity")
                task_object_id = entity.get("id")
                task_used_defined = task.get("user_defined")

                # Update rank if iteration was requested
                if phase_ids in (phase_id, -1):
                    # Instantiate object with retrieved parameters
                    obj = Object(task_object_id, task_time, node_id, user_defined=task_used_defined)
                    # If this iteration was never encountered initialize rank object
                    returned_dict.setdefault(phase_id, Rank(node_id, logger=self.__logger))
                    # Add object to rank given its type
                    if entity.get("migratable"):
                        returned_dict[phase_id].add_migratable_object(obj)
                    else:
                        returned_dict[phase_id].add_sentinel_object(obj)

                    # Print debug information when requested
                    self.__logger.debug(f"Added object {task_object_id}, time = {task_time} to phase {phase_id}")

        return returned_dict, comm_dict
