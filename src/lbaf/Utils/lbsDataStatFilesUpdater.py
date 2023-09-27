"""src/lbaf/Utils/lbsDataStatFilesUpdater.py"""
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
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger
# pylint:disable=C0413:wrong-import-position


class DataStatFilesUpdater:
    """Class validating VT data files according to the defined schema."""

    def __init__(self):
        self.__args: dict = None

    def __parse_args(self):
        """Parse arguments."""
        parser = PromptArgumentParser(
            allow_abbrev=False,
            description="Updates a data file (file path) or a set of files (directory path) with the given schema type",
            prompt_default=True)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--file-path", help="Path to a validated file. Pass only when validating a single file.",
                           default=None)
        group.add_argument("--dir-path", help="Path to directory where files for validation are located.",
                           default="data/challenging_toy_fewer_tasks")
        parser.add_argument(
            "--file-prefix", help="File prefix. Optional. Pass only when --dir_path is provided.", default="toy")
        parser.add_argument(
            "--file-suffix", help="File suffix. Optional. Pass only when --dir_path is provided.", default="json")
        parser.add_argument("--schema-type", help="Schema type. Must be `LBDatafile` or `LBStatsfile`",
                            choices=["LBDatafile", "LBStatsfile"], default="LBDatafile")
        parser.add_argument("--compress-data",
                            help="If output data should be compressed. Default (None) as input data.", default=None)
        self.__args = parser.parse_args()

    @staticmethod
    def __check_if_file_exists(file_path: str) -> bool:
        """Check for existence of a given file. Returns True when file exists."""
        return os.path.isfile(file_path)

    @staticmethod
    def __check_if_dir_exists(dir_path: str) -> bool:
        """Check for existence of a given directory. Returns True when file exists."""
        return os.path.isdir(dir_path)

    @staticmethod
    def __get_files_for_validation(dir_path: str, file_prefix: str, file_suffix: str) -> list:
        """Check for existence of a given directory. Returns True when file exists."""
        list_of_files = os.listdir(dir_path)

        if not list_of_files:
            raise FileNotFoundError(f"Directory: {dir_path} is EMPTY!")

        if file_prefix is None and file_suffix is None:
            print("File prefix and file suffix not given!")
            file_prefix = Counter([file.split('.')[0] for file in list_of_files]).most_common()[0][0]
            print(f"Found most common prefix: {file_prefix}")
            file_suffix = Counter([file.split('.')[-1] for file in list_of_files]).most_common()[0][0]
            print(f"Found most common suffix: {file_suffix}")

        if file_prefix is not None:
            list_of_files = [file for file in list_of_files if file.split('.')[0] == file_prefix]

        if file_suffix is not None:
            list_of_files = [file for file in list_of_files if file.split('.')[-1] == file_suffix]

        return sorted([os.path.join(dir_path, file) for file in list_of_files],
                      key=lambda x: int(x.split(os.sep)[-1].split('.')[-2]))

    def __add_type_to_file(self, file_path):
        """Add given type to the file. """
        print(f"Adding schema to file: {file_path}")
        file_uncompressed = None
        if self.__args.compress_data is None:
            file_uncompressed = 0
        elif self.__args.compress_data is not None:
            if self.__args.compress_data:
                file_uncompressed = 0
            else:
                file_uncompressed = 1

        with open(file_path, "rb") as compr_json_file:
            compr_bytes = compr_json_file.read()
            try:
                decompr_bytes = brotli.decompress(compr_bytes)
                decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
            except brotli.error:
                if self.__args.compress_data is None:
                    file_uncompressed = 1
                decompressed_dict = json.loads(compr_bytes.decode("utf-8"))

        # Adding schema type to file
        decompressed_dict["type"] = self.__args.schema_type

        json_str = json.dumps(decompressed_dict, separators=(',', ':'))

        if file_uncompressed:
            with open(file_path, "wt", encoding="utf-8") as uncompr_json_file:
                uncompr_json_file.write(json_str)
        else:
            with open(file_path, "wb") as compr_json_file:
                compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
                compr_json_file.write(compressed_str)

    def run(self):
        """Run the DataStatsFilesUpdater logic."""
        # Parse command line arguments
        self.__parse_args()

        if not (self.__args.file_path is None) ^ (self.__args.dir_path is None):
            get_logger().error(
                "One argument value is required for either file-path or dir-path")
            raise SystemExit(1)

        # Get input path as absolute path
        if self.__args.file_path:
            self.__args.file_path = os.path.abspath(self.__args.file_path)
        if self.__args.dir_path:
            self.__args.dir_path = os.path.abspath(self.__args.dir_path)

        if self.__args.file_path is not None:
            if self.__check_if_file_exists(file_path=self.__args.file_path):
                self.__add_type_to_file(file_path=self.__args.file_path)
            else:
                raise FileNotFoundError(f"File: {self.__args.file_path} NOT found!")
        elif self.__args.dir_path is not None:
            if self.__check_if_dir_exists(dir_path=self.__args.dir_path):
                list_of_files_for_validation = self.__get_files_for_validation(dir_path=self.__args.dir_path,
                                                                               file_prefix=self.__args.file_prefix,
                                                                               file_suffix=self.__args.file_suffix)
                for file in list_of_files_for_validation:
                    self.__add_type_to_file(file_path=file)
            else:
                raise FileNotFoundError(f"Directory: {self.__args.dir_path} does NOT exist")
        else:
            raise Exception("FILE path or DIRECTORY path has to be given")


if __name__ == "__main__":
    DataStatFilesUpdater().run()
