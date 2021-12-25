#
#@HEADER
###############################################################################
#
#                              lbsLoadReaderVT.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
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
########################################################################
import csv
import json
import os
import sys

import bcolors
import brotli

from src.IO.schemaValidator import SchemaValidator
from src.Model.lbsObject import Object
from src.Model.lbsObjectCommunicator import ObjectCommunicator
from src.Model.lbsRank import Rank


class LoadReader:
    """A class to read VT Object Map files. These CSV files conform
    to the following format:

      <phase_id/phase>, <object-id>, <time>
      <phase_id/phase>, <object-id1>, <object-id2>, <num-bytes>

    Each file is named as <base-name>.<node>.vom, where <node> spans the number
    of MPI ranks that VT is utilizing.

    Each line in a given file specifies the load of each object that is
    currently mapped to that VT node for a given phase_id/phase. Lines with 3
    entries specify load for an object in term of wall time. Lines with 4
    entries specify the communication volume between objects in bytes.

    Load profile collection and output is enabled in VT with the following flags:

      mpirun -n 4 ./program --vt_lb_stats
                            --vt_lb_stats_dir=my-stats-dir
                            --vt_lb_stats_file=<base-name>
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

    def __init__(self, file_prefix, verbose=False, file_suffix="vom"):
        # The base directory and file name for the log files
        self.file_prefix = file_prefix

        # Data files(data loading) suffix
        self.file_suffix = file_suffix

        # Enable or disable verbose mode
        self.verbose = verbose

    def get_node_trace_file_name(self, node_id):
        """Build the file name for a given rank/node ID
        """

        return f"{self.file_prefix}.{node_id}.{self.file_suffix}"

    def read(self, node_id: int, phase_id: int = -1, comm: bool = False) -> tuple:
        """Read the file for a given node/rank. If phase_id==-1 then all
        steps are read from the file; otherwise, only `phase_id` is.
        """

        # Retrieve file name for given node and make sure that it exists
        file_name = self.get_node_trace_file_name(node_id)
        print(f"{bcolors.HEADER}[LoadReaderVT] {bcolors.END}Reading {file_name} VT object map")
        if not os.path.isfile(file_name):
            print(f"{bcolors.ERR}*  ERROR: [LoadReaderVT] File {file_name} does not exist.{bcolors.END}")
            sys.exit(1)

        # Retrieve communications from JSON reader
        iter_map = {}
        iter_map, comm = self.json_reader(
            returned_dict=iter_map,
            file_name=file_name,
            phase_ids=phase_id,
            node_id=node_id)

        # Print more information when requested
        if self.verbose:
            print(f"{bcolors.HEADER}[LoadReaderVT]{bcolors.END} Finished reading file: {file_name}")

        # Return map of populated ranks per iteration
        return iter_map, comm

    def read_iteration(self, n_p: int, phase_id: int) -> list:
        """Read all the data in the range of ranks [0..n_p) for a given
        iteration `phase_id`. Collapse the iter_map dictionary from `read(..)`
        into a list of ranks to be returned for the given iteration.
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
            except KeyError:
                print(f"{bcolors.ERR}*  ERROR: [LoadReaderVT] Could not retrieve information for rank {p} "
                      f"at time_step {phase_id}{bcolors.END}")
                sys.exit(1)

            # Merge rank communication with existing ones
            for k, v in rank_comm.items():
                if k in communications:
                    c = communications[k]
                    c.get("sent").extend(v.get("sent"))
                    c.get("received").extend(v.get("received"))
                else:
                    communications[k] = v

        # Build dictionnary of rank objects
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
                    sent = {
                        rank_objects_dict.get(c.get("to")):
                        c.get("bytes") for c in
                        obj_comm.get("sent")
                        if rank_objects_dict.get(c.get("to"))}
                    received = {
                        rank_objects_dict.get(c.get("from")):
                        c.get("bytes") for c in
                        obj_comm.get("received")
                        if rank_objects_dict.get(c.get("from"))}
                    rank_obj.set_communicator(ObjectCommunicator(r=received, s=sent))

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

        # Validate schema
        if SchemaValidator().is_valid(schema_to_validate=decompressed_dict):
            print(bcolors.HEADER
                  + "[LoadReaderVT]"
                  + bcolors.END
                  + " Valid JSON schema in  {}".format(file_name))
        else:
            raise SyntaxError(f"{bcolors.ERR}[LoadReaderVT] Invalid JSON schema in {file_name}{bcolors.END}")

        # Define phases from file
        phases = decompressed_dict["phases"]
        comm_dict = {}

        # Handle empty Rank case
        if not phases:
            returned_dict.setdefault(0, Rank(node_id))

        # Iterate over phases
        for phase in phases:
            # Retrieve phase ID
            phase_id = phase["id"]

            # Ccreate communicator dictionary
            comm_dict = {}

            # Temporary communication list to avoid duplicates
            temp_comm = []

            # Add communications to the object
            communications = phase.get("communications")
            if communications and communications not in temp_comm:
                temp_comm.append(communications)
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
                            comm_dict.setdefault(
                                receiver_obj_id,
                                {"sent": [],
                                 "received": []})

                            # Create sender if it does not exist
                            sender_obj_id = c_from.get("id")
                            comm_dict.setdefault(
                                sender_obj_id,
                                {"sent": [],
                                 "received": []})

                            # Create communication edges
                            comm_dict[receiver_obj_id]["received"].append(
                                {"from": c_from.get("id"), "bytes": c_bytes})
                            comm_dict[sender_obj_id]["sent"].append(
                                {"to": c_to.get("id"), "bytes": c_bytes})
                            if self.verbose:
                                print(f"{bcolors.HEADER}[LoadReaderVT]{bcolors.END} Added communication {num} to phase {phase_id}")
                                for k, v in comm.items():
                                    print(f"\t{k}: {v}")

            # Iterate over tasks
            for task in phase["tasks"]:
                task_time = task.get("time")
                task_object_id = task.get("entity").get("id")

                # Update rank if iteration was requested
                if phase_ids in (phase_id, -1):
                    # Instantiate object with retrieved parameters
                    obj = Object(task_object_id, task_time, node_id)

                    # If this iteration was never encoutered initialize rank object
                    returned_dict.setdefault(phase_id, Rank(node_id))

                    # Add object to rank
                    returned_dict[phase_id].add_migratable_object(obj)

                    # Print debug information when requested
                    if self.verbose:
                        print(f"{bcolors.HEADER}[LoadReaderVT]{bcolors.END} Added object {task_object_id}, time = {task_time} to phase {phase_id}")

        return returned_dict, comm_dict

    def csv_reader(self, returned_dict: dict, file_name: str, phase_id, node_id: int) -> tuple:
        """ Reader compatible with previous VT Object Map files (csv)
        """
        # Open specified input file
        with open(file_name, 'r') as f:
            log = csv.reader(f, delimiter=',')
            # Iterate over rows of input file
            comm_dict = {}
            for row in log:
                n_entries = len(row)

                # Handle three-entry case that corresponds to an object load
                if n_entries == 3:
                    # Parsing the three-entry case, thus this format:
                    #   <time_step/phase>, <object-id>, <time>
                    # Converting these into integers and floats before using them or
                    # inserting the values in the dictionary
                    try:
                        phase, o_id = map(int, row[:2])
                        time = float(row[2])
                    except:
                        print(bcolors.ERR
                              + "*  ERROR: [LoadReaderVT] Incorrect row format:".format(row)
                              + bcolors.END)

                    # Update rank if iteration was requested
                    if phase_id in (phase, -1):
                        # Instantiate object with retrieved parameters
                        obj = Object(o_id, time, node_id)

                        # If this iteration was never encoutered initialize rank object
                        returned_dict.setdefault(phase, Rank(node_id))

                        # Add object to rank
                        returned_dict[phase].add_migratable_object(obj)

                        # Print debug information when requested
                        if self.verbose:
                            print(f"{bcolors.HEADER}[LoadReaderVT]{bcolors.END} iteration = {phase}, object id = {o_id}"
                                  f", time = {time}")

                # Handle four-entry case that corresponds to a communication volume
                elif n_entries == 5:
                    continue
                    # Parsing the five-entry case, thus this format:
                    #   <time_step/phase>, <to-object-id>, <from-object-id>, <volume>, <comm-type>
                    # Converting these into integers and floats before using them or
                    # inserting the values in the dictionary
                    print(f"{bcolors.ERR}*  ERROR: [LoadReaderVT] Communication graph unimplemented{bcolors.END}")
                    sys.exit(1)

                # Unrecognized line format
                else:
                    print(f"{bcolors.ERR}** ERROR: [LoadReaderVT] Wrong line length: {row}{bcolors.END}")
                    sys.exit(1)

        return returned_dict, comm_dict
