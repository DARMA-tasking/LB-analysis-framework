import json
import os
import sys

import brotli
from logging import Logger
from multiprocessing import Pool

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
        """ Write one JSON file per rank. """
        sys.setrecursionlimit(25000)
        with Pool() as pool:
            results = pool.imap_unordered(self.json_writer, self.__phase.get_ranks())
            for file_name in results:
                self.__logger.info(f"Saved {file_name}")

    def json_writer(self, rank: Rank) -> str:
        # Create file name for current rank
        file_name = f"{self.__file_stem}.{rank.get_id()}.{self.__suffix}"
        if self.__output_dir is not None:
            file_name = os.path.join(self.__output_dir, file_name)
        # Count number of unsaved objects for sanity
        n_u = 0
        temp_dict = {}
        # Iterate over objects
        for o in rank.get_objects():
            # Write object to file and increment count
            try:
                # writer.writerow([o.get_rank_id(), o.get_id(), o.get_time()])
                rank_id = o.get_rank_id()
                obj_id = o.get_id()
                obj_time = o.get_time()
                if isinstance(temp_dict.get(rank_id, None), list):
                    temp_dict[rank_id].append({
                        "rank_id": rank_id,
                        "obj_id": obj_id,
                        "obj_time": obj_time})
                else:
                    temp_dict[rank_id] = list()
                    temp_dict[rank_id].append({
                        "rank_id": rank_id,
                        "obj_id": obj_id,
                        "obj_time": obj_time})
            except:
                n_u += 1

        dict_to_dump = {}
        dict_to_dump["phases"] = list()
        for rank_id, others_list in temp_dict.items():
            phase_dict = {"tasks": list(), "id": rank_id}
            for task in others_list:
                task_dict = {
                    "load": task["obj_time"],
                    "resource": "cpu",
                    "object": task["obj_id"]}
                phase_dict["tasks"].append(task_dict)
            dict_to_dump["phases"].append(phase_dict)

        json_str = json.dumps(dict_to_dump, separators=(',', ':'))
        compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)

        with open(file_name, "wb") as compr_json_file:
            compr_json_file.write(compressed_str)

        # Sanity check
        if n_u:
            self.__logger.error(f"{n_u} objects could not be written to JSON file {file_name}")
        else:
            self.__logger.info(f"Wrote {len(rank.get_objects())} objects to {file_name}")

        return file_name
