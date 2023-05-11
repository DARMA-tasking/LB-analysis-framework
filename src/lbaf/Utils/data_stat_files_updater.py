import os
import sys

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

import argparse
from collections import Counter
import json

import brotli

from lbaf.Utils.exception_handler import exc_handler


class DataStatFilesUpdater:
    """ Class validating VT data files according do defined schema. """
    def __init__(self, file_path: str = None, dir_path: str = None, file_prefix: str = None, file_suffix: str = None,
                 schema_type: str = "LBDatafile", compress_data: bool = None):
        self.__file_path = file_path
        self.__dir_path = dir_path
        self.__file_prefix = file_prefix
        self.__file_suffix = file_suffix
        self.__schema_type = schema_type
        self.__compress_data = compress_data
        self.__cli()

    def __cli(self):
        """ Support for common line arguments. """
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--dir_path", help="Path to directory where files for validation are located.")
        group.add_argument("--file_path", help="Path to a validated file. Pass only when validating a single file.")
        parser.add_argument("--file_prefix", help="File prefix. Optional. Pass only when --dir_path is provided.")
        parser.add_argument("--file_suffix", help="File suffix. Optional. Pass only when --dir_path is provided.")
        parser.add_argument("--schema_type", help="Schema type. Must be `LBDatafile` or `LBStatsfile`")
        parser.add_argument("--compress_data", help="If output data should be compressed. Default as input data.")
        args = parser.parse_args()
        if args.file_path:
            self.__file_path = os.path.abspath(args.file_path)
        if args.dir_path:
            self.__dir_path = os.path.abspath(args.dir_path)
        if args.file_prefix:
            self.__file_prefix = args.file_prefix
        if args.file_suffix:
            self.__file_suffix = args.file_suffix
        if args.schema_type:
            if args.schema_type in ["LBDatafile", "LBStatsfile"]:
                self.__schema_type = args.schema_type
            else:
                sys.excepthook = exc_handler
                raise TypeError("Schema_type must be: LBDatafile or LBStatsfile")
        if args.compress_data:
            self.__compress_data = args.compress_data


    @staticmethod
    def __check_if_file_exists(file_path: str) -> bool:
        """ Check for existence of a given file. Returns True when file exists. """
        return os.path.isfile(file_path)

    @staticmethod
    def __check_if_dir_exists(dir_path: str) -> bool:
        """ Check for existence of a given directory. Returns True when file exists. """
        return os.path.isdir(dir_path)

    @staticmethod
    def __get_files_for_validation(dir_path: str, file_prefix: str, file_suffix: str) -> list:
        """ Check for existence of a given directory. Returns True when file exists. """
        list_of_files = os.listdir(dir_path)

        if not list_of_files:
            sys.excepthook = exc_handler
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
        """ Add given type to the file. """
        print(f"Adding schema to file: {file_path}")
        file_uncompressed = None
        if self.__compress_data is None:
            file_uncompressed = 0
        elif self.__compress_data is not None:
            if self.__compress_data:
                file_uncompressed = 0
            else:
                file_uncompressed = 1

        with open(file_path, "rb") as compr_json_file:
            compr_bytes = compr_json_file.read()
            try:
                decompr_bytes = brotli.decompress(compr_bytes)
                decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
            except brotli.error:
                if self.__compress_data is None:
                    file_uncompressed = 1
                decompressed_dict = json.loads(compr_bytes.decode("utf-8"))

        # Adding schema type to file
        decompressed_dict["type"] = self.__schema_type

        json_str = json.dumps(decompressed_dict, separators=(',', ':'))

        if file_uncompressed:
            with open(file_path, "wt") as uncompr_json_file:
                uncompr_json_file.write(json_str)
        else:
            with open(file_path, "wb") as compr_json_file:
                compressed_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
                compr_json_file.write(compressed_str)

    def main(self):
        if self.__file_path is not None:
            if self.__check_if_file_exists(file_path=self.__file_path):
                self.__add_type_to_file(file_path=self.__file_path)
            else:
                sys.excepthook = exc_handler
                raise FileNotFoundError(f"File: {self.__file_path} NOT found!")
        elif self.__dir_path is not None:
            if self.__check_if_dir_exists(dir_path=self.__dir_path):
                list_of_files_for_validation = self.__get_files_for_validation(dir_path=self.__dir_path,
                                                                               file_prefix=self.__file_prefix,
                                                                               file_suffix=self.__file_suffix)
                for file in list_of_files_for_validation:
                    self.__add_type_to_file(file_path=file)
            else:
                sys.excepthook = exc_handler
                raise FileNotFoundError(f"Directory: {self.__dir_path} does NOT exist")
        else:
            sys.excepthook = exc_handler
            raise Exception("FILE path or DIRECTORY path has to be given")


if __name__ == "__main__":
    DataStatFilesUpdater().main()
