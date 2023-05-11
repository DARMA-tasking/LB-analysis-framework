import json
import os
import sys

import brotli
from logging import Logger
from multiprocessing.pool import Pool
from multiprocessing import get_context

from ..Model.lbsPhase import Phase
from ..Model.lbsRank import Rank


class VTDataWriter:
    """A class to write load directives for VT as JSON files
        Each file is named as <base-name>.<node>.out, where <node> spans the number
        of MPI ranks that VT is utilizing.
    """

    def __init__(self, phase: Phase, logger: Logger, f: str = "lbs_out", s: str = "json", output_dir=None):
        """Class constructor:
            phase: Phase instance
            f: file name stem
            s: suffix
        """
        # Assign logger to instance variable
        self.__logger = logger

        # Ensure that provided phase has correct type
        if not isinstance(phase, Phase):
            self.__logger.error("Could not write to ExodusII file by lack of a LBS phase")
            return

        # Assign internals
        self.__phase = phase
        self.__file_stem = f"{f}"
        self.__suffix = s
        self.__output_dir = output_dir

    def write(self):
        """Write one JSON file per rank."""
        sys.setrecursionlimit(25000)
        with Pool(context=get_context("fork")) as pool:
            results = pool.imap_unordered(self.json_writer, self.__phase.get_ranks())
            for file_name in results:
                self.__logger.info(f"Saved {file_name}")

    def __create_object_entries(self, rank_id, objects):
        """Create per-object entries to be outputted to JSON."""
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
        file_name = f"{self.__file_stem}.{rank.get_id()}.{self.__suffix}"
        if self.__output_dir is not None:
            file_name = os.path.join(self.__output_dir, file_name)

        # Initialize output dict
        phase_data = {"id": self.__phase.get_id()}
        r_id = rank.get_id()
        output = {
            "metadata": {
                "type": "LBDatafile",
                "rank": r_id},
            "phases": [phase_data]}

        # Create list of objects descriptions
        tasks = self.__create_object_entries(
            r_id, rank.get_migratable_objects())
        tasks += self.__create_object_entries(
            r_id, rank.get_sentinel_objects())
        phase_data["tasks"] = tasks

        # Write file and return its name
        json_str = json.dumps(output, separators=(',', ':'))
        compressed_str = brotli.compress(
            string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
        with open(file_name, "wb") as compr_json_file:
            compr_json_file.write(compressed_str)
        return file_name
