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
    """ A class to write load directives for VT as JSON files
        Each file is named as <base-name>.<node>.out, where <node> spans the number
        of MPI ranks that VT is utilizing.
    """

    def __init__(self, phase: Phase, logger: Logger, f: str = "lbs_out", s: str = "vom", output_dir=None):
        """ Class constructor:
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
        """ Write one JSON file per rank."""
        sys.setrecursionlimit(25000)
        with Pool(context=get_context("fork")) as pool:
            results = pool.imap_unordered(self.json_writer, self.__phase.get_ranks())
            for file_name in results:
                self.__logger.info(f"Saved {file_name}")

    def json_writer(self, rank: Rank) -> str:
        # Create file name for current rank
        file_name = f"{self.__file_stem}.{rank.get_id()}.{self.__suffix}"
        if self.__output_dir is not None:
            file_name = os.path.join(self.__output_dir, file_name)

        # Create list of objects descriptions
        objects = [
            {"obj_id": o.get_id(), "obj_load": o.get_load()}
            for o in rank.get_objects()]
        print("objects on rank", rank.get_id(), ":", objects)

        dict_to_dump = {}
        for rank_id, others_list in object_map.items():
            phase_dict = {"tasks": list(), "id": rank_id}
            for task in others_list:
                task_dict = {
                    "load": task["obj_load"],
                    "resource": "cpu",
                    "object": task["obj_id"]}
                phase_dict["tasks"].append(task_dict)
            dict_to_dump.setdefault("phases", []).append(phase_dict)
        print(dict_to_dump)
        json_str = json.dumps(dict_to_dump, separators=(',', ':'))
        compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)

        # Write file and return its name
        with open(file_name, "wb") as compr_json_file:
            compr_json_file.write(compressed_str)
        return file_name
