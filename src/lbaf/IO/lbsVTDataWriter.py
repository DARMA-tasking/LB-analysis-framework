import json
import multiprocessing as mp
import os
import sys
from logging import Logger

import brotli

from ..Model.lbsPhase import Phase


class VTDataWriter:
    """A class to write load directives for VT as JSON files

    Each file is named as <base-name>.<node>.out, where <node> spans the number
    of MPI ranks that VT is utilizing.
    """

    def __init__(
        self,
        logger: Logger,
        output_dir: str,
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
            unused_params = o.get_unused_params()
            task_data = {
                "entity": {
                    "home": rank_id,
                    "id": o.get_id(),
                    "migratable": migratable,
                    "type": "object",
                },
                "node": rank_id,
                "resource": "cpu",
                "time": o.get_load()
            }
            if unused_params:
                task_data["entity"].update(unused_params)

            user_defined = o.get_user_defined()
            if user_defined:
                task_data["user_defined"] = user_defined

            subphases = o.get_subphases()
            if subphases:
                task_data["subphases"] = subphases

            tasks.append(task_data)

        return tasks

    def __get_communications(self, phase, rank):
        """Create communication entries to be outputted to JSON."""

        # Get initial communications (if any) for current phase
        phase_communications_dict = phase.get_communications()

        # Add empty entries for ranks with no initial communication
        if rank.get_id() not in phase_communications_dict:
            phase_communications_dict[rank.get_id()] = {}

        # Get original communications on current rank
        initial_on_rank_communications = phase_communications_dict[rank.get_id()]

        # Get all objects on current rank
        rank_objects = rank.get_object_ids()

        # Initialize final communications
        communications = []

        # Ensure all objects are on the correct rank
        if initial_on_rank_communications:
            for comm_dict in initial_on_rank_communications:
                if not comm_dict["from"]["migratable"]: # object is sentinel
                    communications.append(comm_dict)
                elif comm_dict["from"]["id"] in rank_objects:
                    communications.append(comm_dict)
                else:
                    self.__moved_comms.append(comm_dict)

        # Loop through any moved objects to find the correct rank
        if self.__moved_comms:
            for moved_dict in self.__moved_comms:
                if moved_dict["from"]["id"] in rank_objects:
                    communications.append(moved_dict)

        return communications

    def serialize(self, phases: dict) -> list:
        """ Create list of serialized JSON per """

        # Ensure that provided phases is a dictionary of Phase instances
        if not isinstance(phases, dict) or not all(
                [isinstance(p, Phase) for p in phases.values()]):
            self.__logger.error(
                "serialize must be passed a dictionary of phases")
            raise SystemExit(1)

        self.__phases = phases

        # Assemble mapping from ranks to their phases
        rank_phases = {}
        for p in phases.values():
            for r in p.get_ranks():
                rank_phases.setdefault(r, {})
                rank_phases[r.get_id()][p.get_id()] = r

        # Serialize each rank's data
        serialized_data_list = []
        for rank_phases_double in rank_phases.items():
            serialized_data = self._json_serializer(rank_phases_double)
            serialized_data_list.append(serialized_data)

        return serialized_data_list

    def _json_serializer(self, rank_phases_double) -> str:
        """Write one JSON per rank for list of phase instances."""
        # Unpack received double
        r_id, r_phases = rank_phases_double

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
                "rank": r_id
            }

        # Initialize output dict
        output = {
            "metadata": metadata,
            "phases": []}

        # Iterate over phases
        for p_id, rank in r_phases.items():
            # Get current phase
            current_phase = self.__phases.get(p_id)

            # Create data to be outputted for current phase
            self.__logger.debug(f"Writing phase {p_id} for rank {r_id}")
            phase_data= {"id": p_id,
                         "tasks":
                            self.__create_tasks(
                                r_id, rank.get_migratable_objects(), migratable=True) +
                            self.__create_tasks(
                                r_id, rank.get_sentinel_objects(), migratable=False),
            }

            # Add communication data (if present)
            communications = self.__get_communications(current_phase, rank)
            if communications:
                phase_data["communications"] = communications

            output["phases"].append(phase_data)

        # Serialize and possibly compress JSON payload
        serial_json = json.dumps(output, separators=(',', ':'))
        return serial_json

    def _json_writer(self, rank_phases_double) -> str:
        """Write one JSON per rank for list of phase instances."""
        # Unpack received double
        r_id, r_phases = rank_phases_double

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
        """ Write one JSON per rank for dictonary of phases."""

        # Ensure that provided phase has correct type
        if not isinstance(phases, dict) or not all(
            [isinstance(p, Phase) for p in phases.values()]):
            self.__logger.error(
                "JSON writer must be passed a dictionary of phases")
            raise SystemExit(1)

        self.__phases = phases

        # Assemble mapping from ranks to their phases
        self.__rank_phases = {}
        for p in phases.values():
            for r in p.get_ranks():
                self.__rank_phases.setdefault(r.get_id(), {})
                self.__rank_phases[r.get_id()][p.get_id()]= r

        # Prevent recursion overruns
        sys.setrecursionlimit(25000)

        # Write individual rank files using data parallelism
        with mp.pool.Pool(context=mp.get_context("fork")) as pool:
            results = pool.imap_unordered(
                self._json_writer, self.__rank_phases.items())
            for file_name in results:
                self.__logger.info(f"Wrote {file_name}")
