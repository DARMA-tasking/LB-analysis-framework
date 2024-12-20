#
#@HEADER
###############################################################################
#
#                              lbsVTDataWriter.py
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
import multiprocessing as mp
import os
import sys
import math
from logging import Logger
from typing import Optional

import brotli

from ..Model.lbsPhase import Phase
from ..Model.lbsRank import Rank
from ..Model.lbsObject import Object


class VTDataWriter:
    """A class to write load directives for VT as JSON files

    Each file is named as <base-name>.<node>.out, where <node> spans the number
    of MPI ranks that VT is utilizing.
    """

    def __init__(
        self,
        logger: Logger,
        output_dir: Optional[str],
        stem: str,
        parameters: dict):
        """Class constructor

        :param phase: Phase instance
        :param stem: file name stem
        :param parameters: a dictionary of parameters
        """
        # Assign logger to instance variable
        self.__logger = logger

        # Useful fields
        self.__rank_phases = None
        self.__phases = None

        # Set up mp manager
        manager = mp.Manager()
        self.__moved_comms = manager.list()
        # self.__to_remove = manager.list()

        # Assign internals
        self.__file_stem = stem
        if output_dir is not None:
            self.__file_stem = os.path.join(
                output_dir, self.__file_stem)
        try:
            self.__extension = parameters["json_output_suffix"]
            self.__compress = parameters["compressed"]
        except Exception as e:
            self.__logger.error(
                f"Missing JSON writer configuration parameter(s): {e}")
            raise SystemExit(1) from e

    def __create_tasks(self, rank_id, objects, migratable):
        """Create per-object entries to be outputted to JSON."""
        tasks = []

        for o in objects:
            task_data = {
                "entity": {
                    "home": rank_id,
                    "migratable": migratable,
                    "type": "object",
                },
                "node": rank_id,
                "resource": "cpu",
                "time": o.get_load()
            }

            entity_properties = o.get_qois("entity_property")
            for prop_name, prop_getter in entity_properties.items():
                if prop_getter() is not None and prop_name != "packed_id":
                    task_data["entity"][prop_name] = prop_getter()

            unused_params = o.get_unused_params()
            if unused_params:
                task_data["entity"].update(unused_params)

            task_data["entity"] = dict(sorted(task_data["entity"].items()))

            user_defined = o.get_user_defined()
            if user_defined:
                task_data["user_defined"] = dict(sorted(user_defined.items()))
            else:
                task_data["user_defined"] = {}

            object_qois = o.get_qois("qoi")
            for qoi_name, qoi_getter in object_qois.items():
                if qoi_getter() is not None:
                    task_data["user_defined"][qoi_name] = qoi_getter()
                else:
                    task_data["user_defined"][qoi_name] = -1

            # Append data for current object
            tasks.append(task_data)

        # Return created tasks on this rank
        return tasks

    def __create_task_data(self, rank: Rank):
        """Create task data."""
        return sorted(
            self.__create_tasks(
                rank.get_id(), rank.get_migratable_objects(), migratable=True) +
            self.__create_tasks(
                rank.get_id(), rank.get_sentinel_objects(), migratable=False),
            key=lambda x: x.get("entity").get(
                "id", x.get("entity").get("seq_id")))

    def __find_object_rank(self, phase: Phase, obj: Object):
        """Determine which rank owns the object."""
        for r in phase.get_ranks():
            if obj in r.get_objects():
                return r

        # If this point is reached the object could not be found
        self.__logger.error(
            f"Object id {object} cannot be located in any rank of phase {phase.get_id()}")
        raise SystemExit(1)

    def __get_communications(self, phase: Phase, rank: Rank):
        """Create communication entries to be outputted to JSON."""

        # Get initial communications (if any) for current phase
        phase_communications_dict = phase.get_communications()

        # Get original communications on current rank
        r_id = rank.get_id()
        phase_communications_dict.setdefault(r_id, {})
        initial_on_rank_communications = phase_communications_dict[r_id]

        # Get all objects on current rank
        rank_objects = rank.get_object_ids()

        # Initialize final communications
        communications = []
        # Ensure all objects are on the correct rank
        if initial_on_rank_communications:
            for comm_entry in initial_on_rank_communications:
                missing_ref = None
                # Copy object information to the communication node
                sender_obj: Object = [o for o in phase.get_objects() if
                    o.get_id() is not None and o.get_id() == comm_entry["from"].get("id") or
                    o.get_seq_id() is not None and o.get_seq_id() == comm_entry["from"].get("seq_id")]
                if len(sender_obj) == 1:
                    # Retrieve communications with single sender
                    sender_obj = sender_obj[0]
                    sender_rank_id = self.__find_object_rank(phase, sender_obj).get_id()
                    from_rank: Rank = [
                        r for r in phase.get_ranks() if r.get_id() == sender_rank_id][0]
                    comm_entry["from"]["home"] = sender_rank_id
                    comm_entry["from"]["migratable"] = from_rank.is_migratable(sender_obj)
                    for k, v in sender_obj.get_unused_params().items():
                        comm_entry["from"][k] = v
                    comm_entry["from"] = dict(sorted(comm_entry["from"].items()))
                else:
                    # Other cases are not supported
                    missing_ref = comm_entry["from"].get("id", comm_entry["from"].get("seq_id"))
                    self.__logger.error(
                        f"Invalid object id ({missing_ref}) in communication {json.dumps(comm_entry)}")

                receiver_obj: Object = [o for o in phase.get_objects() if
                    o.get_id() is not None and o.get_id() == comm_entry["to"].get("id") or
                    o.get_seq_id() is not None and o.get_seq_id() == comm_entry["to"].get("seq_id")]
                if len(receiver_obj) == 1:
                    # Retrieve communications with single receiver
                    receiver_obj = receiver_obj[0]
                    receiver_rank_id = self.__find_object_rank(phase, receiver_obj).get_id()
                    comm_entry["to"]["home"] = receiver_rank_id
                    to_rank: Rank = [
                        r for r in phase.get_ranks() if receiver_obj in r.get_objects()][0]
                    comm_entry["to"]["migratable"] = to_rank.is_migratable(receiver_obj)
                    for k, v in receiver_obj.get_unused_params().items():
                        comm_entry["to"][k] = v
                    comm_entry["to"] = dict(sorted(comm_entry["to"].items()))
                else:
                    # Other cases are not supported
                    missing_ref = comm_entry["to"].get("id", comm_entry["to"].get("seq_id"))
                    self.__logger.error(
                        f"Invalid object id ({missing_ref}) in communication {json.dumps(comm_entry)}")

                if missing_ref is not None:
                    # Keep communication with invalid entity references for the moment.
                    # We might remove these communications in the future in the reader work to fix invalid input.
                    self.__logger.warning(
                        f"Missing reference: ({missing_ref}) in communication {json.dumps(comm_entry)}")
                    communications.append(comm_entry)
                elif ("migratable" in comm_entry["from"].keys() and
                        not comm_entry["from"]["migratable"]):
                    # Object is sentinel
                    communications.append(comm_entry)
                elif comm_entry["from"].get(
                        "id", comm_entry["from"].get("seq_id")) in rank_objects:
                    communications.append(comm_entry)
                else:
                    self.__moved_comms.append(comm_entry)

        # Loop through any moved objects to find the correct rank
        if self.__moved_comms:
            for moved_dict in self.__moved_comms:
                if moved_dict["from"].get("id", moved_dict["from"].get("seq_id")) in rank_objects:
                    communications.append(moved_dict)

        # Return created list of communications
        return communications

    def _json_serializer(self, rank_phases_double) -> str:
        """Write one JSON per rank for list of phase instances."""
        # Unpack received double
        r_id, r_phases = rank_phases_double
        current_rank = None
        # Get current rank
        for p_id, rank in r_phases.items():
            if rank.get_id() == r_id:
                current_rank = rank

        # Get metadata
        if current_rank.get_metadata():
            metadata = current_rank.get_metadata()
        else:
            metadata = {
                "type": "LBDatafile",
                "rank": r_id}

        # Initialize output dict
        output = {
            "metadata": metadata,
            "phases": []}

        # Iterate over phases
        for p_id, rank in r_phases.items():
            # Get current phase tuple and phase
            self.__logger.debug(f"Writing phase {p_id} for rank {r_id}")
            current_phase = self.__phases.get(p_id)

            # Get rank info and QOIs
            rank_info : Rank = [r for r in current_phase.get_ranks() if r.get_id() == r_id][0]
            rank_qois = rank_info.get_qois()

            # Create data to be outputted for current phase
            phase_data = {
                "id": p_id,
                "tasks": self.__create_task_data(rank),
                "user_defined": {
                    qoi_name: qoi_getter() for qoi_name, qoi_getter in rank_qois.items()
                    if qoi_name != "homed_blocks_ratio" # omit for now because it might be nan
                },
            }

            # JSON can not handle nan so make this ratio -1 when it's not valid
            homed_ratio = -1
            if not math.isnan(rank_info.get_homed_blocks_ratio()):
                homed_ratio = rank_info.get_homed_blocks_ratio()
            phase_data["user_defined"]["num_homed_ratio"] = homed_ratio

            # Add communication data if present
            communications = self.__get_communications(current_phase, rank)
            if communications:
                phase_data["communications"] = communications

            # Add load balancing iterations if present
            lb_iterations = current_phase.get_lb_iterations()
            if lb_iterations:
                phase_data["lb_iterations"] = []
                # Iterate over load balancing iterations
                for it in lb_iterations:
                    # Create data dict for load balancing iteration
                    it_id = it.get_sub_id()
                    self.__logger.debug(
                        f"Writing iteration {it_id} of phase {p_id} for rank {r_id}")
                    iteration_data = {"id": it_id}

                    # Retrieve same rank in load balancing iteration
                    for it_r in it.get_ranks():
                        if r_id != it_r.get_id():
                            continue

                        # Add task data for current rank in iteration
                        iteration_data["tasks"] = self.__create_task_data(it_r)

                        # Add communication data if present
                        communications = self.__get_communications(it, it_r)
                        if communications:
                            iteration_data["communications"] = communications

                        # Append load balancing iteration to phase data
                        phase_data["lb_iterations"].append(iteration_data)

            # Append create phase
            output["phases"].append(phase_data)

        # Serialize and possibly compress JSON payload
        serial_json = json.dumps(output, separators=(',', ':'))
        return serial_json

    def _json_writer(self, rank_phases_double) -> str:
        """Write one JSON per rank for list of phase instances."""
        # Unpack received double
        r_id = rank_phases_double[0]

        # Create file name for current rank
        file_name = f"{self.__file_stem}.{r_id}.{self.__extension}"
        self.__logger.debug(f"Writing {file_name}")

        # Serialize and possibly compress JSON payload
        serial_json = self._json_serializer(rank_phases_double)

        if self.__compress:
            serial_json = brotli.compress(
                string=serial_json.encode("utf-8"), mode=brotli.MODE_TEXT)
        with open(file_name, "wb" if self.__compress else 'w') as json_file:
            json_file.write(serial_json)

        # Return JSON file name
        return file_name

    def write(self, phases: dict):
        """ Write one JSON per rank for dictonary of phases with possibly iterations."""

        # Ensure that provided phase has correct type
        if not isinstance(phases, dict):
            self.__logger.error(
                "JSON writer must be passed a dictionary")
            raise SystemExit(1)
        self.__phases = phases

        # Assemble mapping from ranks to their phases
        self.__rank_phases = {}
        for phase in self.__phases.values():
            # Handle case where entry only cintains a phase
            for r in phase.get_ranks():
                self.__rank_phases.setdefault(r.get_id(), {})
                self.__rank_phases[r.get_id()][phase.get_id()] = r

        # Prevent recursion overruns
        sys.setrecursionlimit(25000)

        # Write individual rank files using data parallelism
        with mp.pool.Pool(context=mp.get_context("fork")) as pool:
            results = pool.imap_unordered(
                self._json_writer, self.__rank_phases.items())
            for file_name in results:
                self.__logger.info(f"Wrote {file_name}")
