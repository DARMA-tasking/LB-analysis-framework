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

        # Initialize storage
        iter_map = dict()

        # iter_map, comm = self.csv_reader(returned_dict=iter_map, file_name=file_name, phase_id=phase_id,
        #                                  node_id=node_id)
        iter_map, comm = self.json_reader(returned_dict=iter_map, file_name=file_name, phase_ids=phase_id,
                                          node_id=node_id)

        # Print more information when requested
        if self.verbose:
            print(f"{bcolors.HEADER}[LoadReaderVT]{bcolors.END} Finished reading file: {file_name}")

        # Return map of populated processors per iteration
        return iter_map, comm

    def read_iteration(self, n_p: int, phase_id: int) -> list:
        """Read all the data in the range of procs [0..n_p) for a given
        iteration `phase_id`. Collapse the iter_map dictionary from `read(..)`
        into a list of processors to be returned for the given iteration.
        """

        # Create storage for processors
        procs = [None] * n_p
        communication = dict()

        # Iterate over all processors
        for p in range(n_p):
            # Read data for given iteration and assign it to processor
            # proc_iter_map = self.read(p, phase_id)
            proc_iter_map, proc_comm = self.read(p, phase_id)

            # Try to retrieve processor information at given time-step
            try:
                procs[p] = proc_iter_map[phase_id]
                communication[p] = proc_comm
            except KeyError:
                print(f"{bcolors.ERR}*  ERROR: [LoadReaderVT] Could not retrieve information for processor {p} "
                      f"at time_step {phase_id}{bcolors.END}")
                sys.exit(1)

        # Adding communication
        proc_objects_set = set()
        for proc in procs:
            proc_objects_set.update(proc.get_objects())
        proc_objects_dict = {obj.get_id(): obj for obj in proc_objects_set}

        # iterating over processors
        for proc_num, proc in enumerate(procs):
            # iteration over objects in processor
            for proc_obj in proc.get_objects():
                obj_id = proc_obj.get_id()
                # checking if there is any communication for the object
                obj_communication = communication.get(proc_num, None).get(obj_id, None)
                if obj_communication is not None:
                    send = {proc_objects_dict.get(snd.get("to"), None): snd.get("bytes") for snd in
                            obj_communication.get("send") if proc_objects_dict.get(snd.get("to"), None) is not None}
                    received = {proc_objects_dict.get(snd.get("from"), None): snd.get("bytes") for snd in
                                obj_communication.get("received") if
                                proc_objects_dict.get(snd.get("from"), None) is not None}
                    proc_obj.set_communicator(ObjectCommunicator(r=received, s=send))

        # Return populated list of processors
        return procs

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

        # validate schema
        if SchemaValidator().is_valid(schema_to_validate=decompressed_dict):
            print(f"{bcolors.OK}[LoadReaderVT] Valid JSON schema in {file_name}{bcolors.END}")
        else:
            raise SyntaxError(f"{bcolors.ERR}[LoadReaderVT] Invalid JSON schema in {file_name}{bcolors.END}")

        # defining phases from file
        phases = decompressed_dict["phases"]
        comm_dict = dict()
        # iterating over phases
        for phase in phases:
            # creating communicator dictionary
            comm_dict = dict()
            # temporary communication list, to avoid duplicates in communication
            temp_comm = list()
            phase_id = phase["id"]
            # adding communications to the object
            communications = phase.get("communications", None)
            # as communications is optional, there is a need to check if exists
            if communications is not None and communications not in temp_comm:
                temp_comm.append(communications)
                for num, comm in enumerate(communications):
                    type_ = comm.get("type", None)
                    to_ = comm.get("to", None)
                    from_ = comm.get("from", None)
                    bytes_ = comm.get("bytes", None)
                    # supports only SendRecv communication type
                    if type_ == "SendRecv":
                        # checking if both are objects
                        if to_.get("type", None) == "object" and from_.get("type", None) == "object":
                            # if no sender or receiver exists, then creating one
                            receiver_obj_id = to_.get("id", None)
                            sender_obj_id = from_.get("id", None)

                            if comm_dict.get(receiver_obj_id, None) is None:
                                comm_dict[receiver_obj_id] = dict()
                                comm_dict[receiver_obj_id]["send"] = list()
                                comm_dict[receiver_obj_id]["received"] = list()

                            if comm_dict.get(sender_obj_id, None) is None:
                                comm_dict[sender_obj_id] = dict()
                                comm_dict[sender_obj_id]["send"] = list()
                                comm_dict[sender_obj_id]["received"] = list()

                            comm_dict[receiver_obj_id]["received"].append(
                                {"from": from_.get("id", None), "bytes": bytes_})
                            if self.verbose:
                                print(f"{bcolors.BLUE}[LoadReaderVT] Added received Phase:{phase_id}, Comm num: {num}\n"
                                      f"\t\t\tCommunication entry: {comm}{bcolors.END}")
                            comm_dict[sender_obj_id]["send"].append({"to": to_.get("id", None), "bytes": bytes_})
                            if self.verbose:
                                print(f"{bcolors.BLUE}[LoadReaderVT] Added sent Phase:{phase_id}, Comm num: {num}\n"
                                      f"\t\t\tCommunication entry: {comm}{bcolors.END}")

            for task in phase["tasks"]:
                task_time = task.get("time")
                task_object_id = task.get("entity").get("id")

                # Update processor if iteration was requested
                if phase_ids in (phase_id, -1):
                    # Instantiate object with retrieved parameters
                    obj = Object(task_object_id, task_time, node_id)

                    # If this iteration was never encoutered initialize proc object
                    returned_dict.setdefault(phase_id, Rank(node_id))

                    # Add object to processor
                    returned_dict[phase_id].add_migratable_object(obj)

                    # Print debug information when requested
                    if self.verbose:
                        print(f"{bcolors.HEADER}[LoadReaderVT] {bcolors.END}iteration = {phase_id}, "
                              f"object id = {task_object_id}, time = {task_time}")

        return returned_dict, comm_dict

    def csv_reader(self, returned_dict: dict, file_name: str, phase_id, node_id: int) -> tuple:
        """ Reader compatible with previous VT Object Map files (csv)
        """
        # Open specified input file
        with open(file_name, 'r') as f:
            log = csv.reader(f, delimiter=',')
            # Iterate over rows of input file
            comm_dict = dict()
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

                    # Update processor if iteration was requested
                    if phase_id in (phase, -1):
                        # Instantiate object with retrieved parameters
                        obj = Object(o_id, time, node_id)

                        # If this iteration was never encoutered initialize proc object
                        returned_dict.setdefault(phase, Rank(node_id))

                        # Add object to processor
                        returned_dict[phase].add_migratable_object(obj)

                        # Print debug information when requested
                        if self.verbose:
                            print(f"{bcolors.HEADER}[LoadReaderVT]{bcolors.END} iteration = {phase}, object id = {o_id}"
                                  f", time = {time}")

                # Handle four-entry case that corresponds to a communication weight
                elif n_entries == 5:
                    continue
                    # Parsing the five-entry case, thus this format:
                    #   <time_step/phase>, <to-object-id>, <from-object-id>, <weight>, <comm-type>
                    # Converting these into integers and floats before using them or
                    # inserting the values in the dictionary
                    print(f"{bcolors.ERR}*  ERROR: [LoadReaderVT] Communication graph unimplemented{bcolors.END}")
                    sys.exit(1)

                # Unrecognized line format
                else:
                    print(f"{bcolors.ERR}** ERROR: [LoadReaderVT] Wrong line length: {row}{bcolors.END}")
                    sys.exit(1)

        return returned_dict, comm_dict
