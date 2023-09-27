import csv
import importlib
import json
import os
import sys
from collections import Counter

import brotli

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger
# pylint:disable=C0413:wrong-import-position


class Csv2JsonConverter:
    """A class to convert from previous log structure (CSV) to a current log structure (JSON)
    with/without Brotli compression.

    Files for conversion should be named as follows 'prefix.rank/node.extension' e.g. 'data.0.csv', 'data.1.csv'
    Changes input CSV files e.g. <time_step/phase>, <object-id>, <time> to JSON:
    {"phases":[
        {"tasks":[
            {"time":0.036448,"resource":"cpu","object":51539607559,"node":7},
            {"time":0.0298901,"resource":"cpu","object":47244640263,"node":7}
            ],
        "id":0}]}
    """

    def __init__(self):
        self.__args = None

    def __parse_args(self):
        """Parse arguments."""
        parser = PromptArgumentParser(allow_abbrev=False, prompt_default=True)
        parser.add_argument("--dir", help="Absolute dir path or relative(from project path)",
                            default="data/vt_example_lb_data")
        parser.add_argument("--output-dir", help="Absolute dir path or relative(from project path)",
                            default=os.path.join(PROJECT_PATH, "output", "converted_data"))
        parser.add_argument("--compressed", help="If output file should be compressed", type=bool, default=True)
        parser.add_argument("--in-file-name-prefix", help="Input file name prefix e.g. 'data'", default="data")
        parser.add_argument("--in-file-extension", help="Input file extension, e.g. '.csv'", default=".vom")
        self.__args = parser.parse_args()

    @staticmethod
    def _get_data_dir(dir_path: str) -> str:
        """Return a path to data directory."""

        if os.path.isdir(dir_path):
            return dir_path
        if os.path.isdir(os.path.join(PROJECT_PATH, dir_path)):
            return os.path.join(PROJECT_PATH, dir_path)
        else:
            get_logger().error(
                f"Can not find dir {dir_path}")
            raise SystemExit(1)

    def _get_files_for_conversion(self) -> list:
        """Return list of tuples as follows (file_to_convert_path, converted_file_path)."""
        # Defining output path and creating if not exists
        output_path = os.path.join(PROJECT_PATH, self.__args.output_dir)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Getting files paths
        if self.__args.in_file_extension is not None and self.__args.in_file_name_prefix is not None:
            dir_list = [(os.path.join(self.__args.data_dir, file), os.path.join(output_path, file)) for file in
                        os.listdir(self.__args.data_dir) if os.path.isfile(os.path.join(self.__args.data_dir, file)) and
                        os.path.splitext(file)[-1] == self.__args.in_file_extension and
                        file.split('.')[0] == self.__args.in_file_name_prefix]
        elif self.__args.in_file_extension is not None and self.__args.in_file_name_prefix is None:
            dir_list = [(os.path.join(self.__args.data_dir, file), os.path.join(output_path, file)) for file in
                        os.listdir(self.__args.data_dir) if os.path.isfile(os.path.join(self.__args.data_dir, file)) and
                        os.path.splitext(file)[-1] == self.__args.in_file_extension]
        elif self.__args.in_file_extension is None and self.__args.in_file_name_prefix is not None:
            dir_list = [(os.path.join(self.__args.data_dir, file), os.path.join(output_path, file)) for file in
                        os.listdir(self.__args.data_dir) if os.path.isfile(os.path.join(self.__args.data_dir, file)) and
                        file.split('.')[0] == self.__args.in_file_name_prefix]
        else:
            prefix_list = [file.split('.')[0] for file in os.listdir(self.__args.data_dir) if
                           os.path.isfile(os.path.join(self.__args.data_dir, file))]
            extenion_list = [os.path.splitext(file)[-1] for file in os.listdir(self.__args.data_dir) if
                             os.path.isfile(os.path.join(self.__args.data_dir, file))]
            most_common_prefix = Counter(prefix_list).most_common(1)[0][0]
            most_common_extension = Counter(extenion_list).most_common(1)[0][0]
            dir_list = [(os.path.join(self.__args.data_dir, file), os.path.join(output_path, file)) for file in
                        os.listdir(self.__args.data_dir) if os.path.isfile(os.path.join(self.__args.data_dir, file)) and
                        os.path.splitext(file)[-1] == most_common_extension and
                        file.split('.')[0] == most_common_prefix]

        print("Files for conversion :")
        for file in dir_list:
            print(f"=> {file[0]}")

        return dir_list

    def _convert_file(self, file_path: tuple) -> None:
        """Convert a file and saves converted file to given path."""
        file_to_convert = file_path[0]
        node = int(os.path.split(file_to_convert)[-1].split('.')[-2])
        file_to_save = file_path[1]
        read_file_list = self._read_csv(file_to_read=file_to_convert)
        read_file_dict = self._get_data_phase_sorted(data=read_file_list)
        self._write_json(
            output_path=file_to_save,
            data_to_convert=read_file_dict,
            node=node)

    @staticmethod
    def _read_csv(file_to_read: str) -> list:
        """Read CSV and returns a list of dicts (phase, object_id, time) ready to save into JSON."""
        # Parse CSV file lines
        with open(file_to_read, "rt", encoding="utf-8") as csv_file:
            log = csv.reader(csv_file, delimiter=',')
            read_list = [{
                "phase_id": int(row[0]),
                "obj_id": int(row[1]),
                "obj_time": float(row[2])}
                for row in log if len(row) == 3]

        # Return read list
        return read_list

    @staticmethod
    def _get_data_phase_sorted(data: list) -> dict:
        """Sort data with respect to the phase. Return dict with phases as keys."""
        # Create temporary dict so rows are sorted by phase_id
        temp_dict = dict()
        for dict_ in data:
            phase_id = dict_.get("phase_id", None)
            obj_id = dict_.get("obj_id", None)
            obj_time = dict_.get("obj_time", None)
            if isinstance(temp_dict.get(phase_id, None), list):
                temp_dict[phase_id].append({
                    "phase_id": phase_id,
                    "obj_id": obj_id,
                    "obj_time": obj_time})
            else:
                temp_dict[phase_id] = []
                temp_dict[phase_id].append({
                    "phase_id": phase_id,
                    "obj_id": obj_id,
                    "obj_time": obj_time})

        # Return temporary dict
        return temp_dict

    def _write_json(self, output_path: str, data_to_convert: dict, node: int) -> None:
        """Convert data to JSON and saves to output path."""
        # Creating dictionary with right structure, which will be dumped
        dict_to_dump = {}
        dict_to_dump["phases"] = []
        for rank_id, others_list in data_to_convert.items():
            phase_dict = {"tasks": [], "id": rank_id}
            for task in others_list:
                task_dict = {
                    "time": task["obj_time"],
                    "resource": "cpu",
                    "entity": {
                        "id": task["obj_id"],
                        "type": "object"},
                    "node": node}
                phase_dict["tasks"].append(task_dict)
            dict_to_dump["phases"].append(phase_dict)

        json_str = json.dumps(dict_to_dump, separators=(',', ':'))
        if self.__args.compressed:
            compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
            with open(output_path, "wb") as compr_json_file:
                compr_json_file.write(compressed_str)
        else:
            with open(output_path, "wt", encoding="utf-8") as json_file:
                json_file.write(json_str)

    def run(self):
        """Get lists of files to convert. Iterate over it and converts each file."""
        # Parse command line arguments
        self.__parse_args()
        self.__args.data_dir = self._get_data_dir(self.__args.dir)

        files_to_convert = self._get_files_for_conversion()
        print("Generated files:")
        for file in files_to_convert:
            self._convert_file(file_path=file)
            print(file[1])


if __name__ == "__main__":
    Csv2JsonConverter().run()
