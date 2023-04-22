import json
import os
import sys
import brotli
import multiprocessing as mp
from logging import Logger

from ..Model.lbsPhase import Phase
from ..Model.lbsRank import Rank


class VTDataWriter:
    """ A class to write load directives for VT as JSON files
        Each file is named as <base-name>.<node>.out, where <node> spans the number
        of MPI ranks that VT is utilizing.
    """

    def __init__(
        self,
        logger: Logger,
        output_dir: str,
        stem: str,
        parameters: dict):
        """ Class constructor:
            phase: Phase instance
            stem: file name stem
            parameters: a dictionary of parameters
        """
        # Assign logger to instance variable
        self.__logger = logger

        # Assign internals
        self.__file_stem = stem
        if output_dir is not None:
            self.__file_stem = os.path.join(
                output_dir, self.__file_stem)
        try:
            self.__extension = parameters["json_output_suffix"]
            self.__compress = parameters["compressed"]
        except Exception as ex:
            self.logger.error("Missing JSON writer configuration parameter(s): %s", ex)
            sys.excepthook = exc_handler
            raise SystemExit(1) from ex

    def __create_tasks(self, rank_id, objects):
        """ Create per-object entries to be outputted to JSON."""
        return [{
            "entity": {
                "home": rank_id,
                "id": o.get_id(),
                "type": "object",
                "migratable": True},
            "node": rank_id,
            "resource": "cpu",
            "time": o.get_load()}
            for o in objects]

    def _json_writer(self, rank: Rank) -> str:
        # Create file name for current rank
        file_name = f"{self.__file_stem}.{rank.get_id()}.{self.__extension}"

        # Initialize output dict
        phase_data = {"id": self.__phase.get_id()}
        r_id = rank.get_id()
        output = {
            "metadata": {
                "type": "LBDatafile",
                "rank": r_id},
            "phases": [phase_data]}

        # Create list of object descriptions
        phase_data["tasks"] = self.__create_tasks(
            r_id, rank.get_migratable_objects()) + self.__create_tasks(
            r_id, rank.get_sentinel_objects())

        # Serialize and possibly compress JSON payload
        serial_json = json.dumps(output, separators=(',', ':'))
        if self.__compress:
            serial_json = brotli.compress(
                string=serial_json.encode("utf-8"), mode=brotli.MODE_TEXT)
        with open(file_name, "wb" if self.__compress else 'w') as json_file:
            json_file.write(serial_json)

        # Return JSON file name
        return file_name

    def write(self, phases: list):
        """ Write one JSON per rank for list of phase instances."""
        # Ensure that provided phase has correct type
        if not isinstance(phases, list) or not all(
            [isinstance(p, Phase) for p in phases]):
            self.__logger.error("JSON writer must be passed a list of Phase instances")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Keep track of phase to be written
        self.__phase_ranks = phases
        for p in phases:
            print(p.get_id(), p)
        sys.exit(1)
        # Prevent recursion overruns
        sys.setrecursionlimit(25000)

        # Write individual rank files using data parallelism
        with mp.pool.Pool(context=mp.get_context("fork")) as pool:
            results = pool.imap_unordered(
                self._json_writer, self.__phases[0].get_ranks())
            for file_name in results:
                self.__logger.info(
                    f"Wrote JSON file: {file_name}")

