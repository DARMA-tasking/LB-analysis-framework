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
        return [{
            "entity": {
                "home": rank_id,
                "id": o.get_id(),
                "migratable": migratable,
                "type": "object",
            },
            "node": rank_id,
            "resource": "cpu",
            "time": o.get_load()}
            for o in objects]

    def _json_writer(self, rank_phases_double) -> str:
        """Write one JSON per rank for list of phase instances."""
        # Unpack received double
        r_id, r_phases = rank_phases_double

        # Create file name for current rank
        file_name = f"{self.__file_stem}.{r_id}.{self.__extension}"
        self.__logger.debug(f"Writing {file_name}")

        # Initialize output dict
        output = {
            "metadata": {
                "type": "LBDatafile",
                "rank": r_id},
            "phases": []}

        # Iterate over phases
        for p_id, rank in r_phases.items():
            # Create data to be outputted for current phase
            self.__logger.debug(f"Writing phase {p_id} for rank {r_id}")
            phase_data = {"id": p_id}
            phase_data["tasks"] = self.__create_tasks(
                r_id, rank.get_migratable_objects(), migratable=True) + self.__create_tasks(
                r_id, rank.get_sentinel_objects(), migratable=False)
            output["phases"].append(phase_data)

        # Serialize and possibly compress JSON payload
        serial_json = json.dumps(output, separators=(',', ':'))
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
