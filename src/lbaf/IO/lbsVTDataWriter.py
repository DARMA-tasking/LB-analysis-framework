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
        output_dir='.',
        stem: str = "LBAF_out",
        ext: str = "json"):
        """ Class constructor:
            phase: Phase instance
            stem: file name stem
            ext: file name extension
        """
        # Assign logger to instance variable
        self.__logger = logger

        # Assign internals
        self.__file_stem = stem
        if output_dir is not None:
            self.__file_stem = os.path.join(
                output_dir, self.__file_stem)
        self.__extension = ext

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

    def json_writer(self, rank: Rank) -> str:
        # Create file name for current rank
        file_name = f"{self.__file_stem}.{rank.get_id()}.{self.__extension}"

        # Initialize output dict
        phase_data = {"id": self.__phase.get_id() + self.__increment}
        r_id = rank.get_id()
        output = {
            "metadata": {
                "type": "LBDatafile",
                "rank": r_id},
            "phases": [phase_data]}

        # Create list of objects descriptions
        phase_data["tasks"] = self.__create_tasks(
            r_id, rank.get_migratable_objects()) + self.__create_tasks(
            r_id, rank.get_sentinel_objects())

        # Write file and return its name
        json_str = json.dumps(output, separators=(',', ':'))
        compressed_str = brotli.compress(
            string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
        with open(file_name, "wb") as compr_json_file:
            compr_json_file.write(compressed_str)
        return file_name

    def write(self, phase: Phase, increment: int):
        """ Write one JSON per rank for given phase instance."""
        # Ensure that provided phase has correct type
        if not isinstance(phase, Phase):
            self.__logger.error("Cannot write to JSON file without a Phase instance")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Set member variables
        self.__phase = phase
        self.__increment = increment

        # Prevent recursion overruns
        sys.setrecursionlimit(25000)

        # Write individual rank files using data parallelism
        with mp.pool.Pool(context=mp.get_context("fork")) as pool:
            results = pool.imap_unordered(
                self.json_writer, self.__phase.get_ranks())
            for file_name in results:
                self.__logger.info(
                    f"Wrote JSON file: {file_name}")
