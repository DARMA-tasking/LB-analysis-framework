import os
import json
import brotli
from logging import Logger


from ..Model.lbsPhase import Phase
from ..Model.lbsRank import Rank


class VTDataWriter:
    """ A class to write load directives for VT as JSON files
        Each file is named as <base-name>.<node>.out, where <node> spans the number
        of MPI ranks that VT is utilizing.
    """

    def __init__(self, phase: Phase, f: str = "lbs_out", s: str = "vom", output_dir=None, logger: Logger = None):
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
        """Write one JSON file per rank with the following format:
            <phase-id>, <object-id>, <time>
        """
        # Iterate over ranks
        for p in self.__phase.get_ranks():
            # Create file name for current rank
            file_name = f"{self.__file_stem}.{p.get_id()}.{self.__suffix}"

            if self.__output_dir is not None:
                file_name = os.path.join(self.__output_dir, file_name)

            # Count number of unsaved objects for sanity
            n_u = 0

            self.json_writer(file_name=file_name, n_u=n_u, rank=p)

    def json_writer(self, file_name: str, n_u: int, rank: Rank):
        temp_dict = {}
        # Iterate over objects
        for o in rank.get_objects():
            # Write object to file and increment count
            try:
                # writer.writerow([o.get_rank_id(), o.get_id(), o.get_time()])
                proc_id = o.get_rank_id()
                obj_id = o.get_id()
                obj_time = o.get_time()
                if isinstance(temp_dict.get(proc_id, None), list):
                    temp_dict[proc_id].append({'proc_id': proc_id, 'obj_id': obj_id, 'obj_time': obj_time})
                else:
                    temp_dict[proc_id] = list()
                    temp_dict[proc_id].append({'proc_id': proc_id, 'obj_id': obj_id, 'obj_time': obj_time})
            except:
                n_u += 1

        dict_to_dump = {}
        dict_to_dump['phases'] = list()
        for proc_id, others_list in temp_dict.items():
            phase_dict = {'tasks': list(), 'id': proc_id}
            for task in others_list:
                task_dict = {'time': task['obj_time'], 'resource': 'cpu', 'object': task['obj_id']}
                phase_dict['tasks'].append(task_dict)
            dict_to_dump['phases'].append(phase_dict)

        json_str = json.dumps(dict_to_dump, separators=(',', ':'))
        compressed_str = brotli.compress(string=json_str.encode('utf-8'), mode=brotli.MODE_TEXT)

        with open(file_name, 'wb') as compr_json_file:
            compr_json_file.write(compressed_str)

        # Sanity check
        if n_u:
            self.__logger.error(f"{n_u} objects could not be written to JSON file {file_name}")
        else:
            self.__logger.info(f"Wrote {len(rank.get_objects())} objects to {file_name}")
