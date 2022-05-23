import os
import sys

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    sys.exit(1)

import argparse
from collections import Counter
import json

import brotli

from lbaf.IO.schemaValidator import SchemaValidator


class JSONDataFilesValidator:
    """ Class validating VT data files according do defined schema. """
    def __init__(self, file_path: str = None, dir_path: str = None, file_prefix: str = None, file_suffix: str = None):
        self.__file_path = file_path
        self.__dir_path = dir_path
        self.__file_prefix = file_prefix
        self.__file_suffix = file_suffix
        self.__cli()

    def __cli(self):
        """ Support for common line arguments. """
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--dir_path", help="Path to directory where files for validation are located.")
        group.add_argument("--file_path", help="Path to a validated file. Pass only when validating a single file.")
        parser.add_argument("--file_prefix", help="File prefix. Optional. Pass only when --dir_path is provided.")
        parser.add_argument("--file_suffix", help="File suffix. Optional. Pass only when --dir_path is provided.")
        args = parser.parse_args()
        if args.file_path:
            self.__file_path = os.path.abspath(args.file_path)
        if args.dir_path:
            self.__dir_path = os.path.abspath(args.dir_path)
        if args.file_prefix:
            self.__file_prefix = args.file_prefix
        if args.file_suffix:
            self.__file_suffix = args.file_suffix

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

    @staticmethod
    def __validate_file(file_path):
        """ Validates the file against the schema. """
        print(f"Validating file: {file_path}")
        with open(file_path, "rb") as compr_json_file:
            compr_bytes = compr_json_file.read()
            try:
                decompr_bytes = brotli.decompress(compr_bytes)
                decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
            except brotli.error:
                decompressed_dict = json.loads(compr_bytes.decode("utf-8"))

        # Extracting type from JSON data
        schema_type = decompressed_dict.get("type")
        if schema_type is not None:
            # Validate schema
            if SchemaValidator(schema_type=schema_type).is_valid(schema_to_validate=decompressed_dict):
                print(f"Valid JSON schema in {file_path}")
            else:
                print(f"Invalid JSON schema in {file_path}")
                SchemaValidator(schema_type=schema_type).validate(schema_to_validate=decompressed_dict)
        else:
            print(f"Schema type not found in file: {file_path}. \nPassing by default when schema type not found.")

    def main(self):
        if self.__file_path is not None:
            if self.__check_if_file_exists(file_path=self.__file_path):
                self.__validate_file(file_path=self.__file_path)
            else:
                print(f"File: {self.__file_path} does NOT exist!")
                sys.exit(1)
        elif self.__dir_path is not None:
            if self.__check_if_dir_exists(dir_path=self.__dir_path):
                list_of_files_for_validation = self.__get_files_for_validation(dir_path=self.__dir_path,
                                                                               file_prefix=self.__file_prefix,
                                                                               file_suffix=self.__file_suffix)
                for file in list_of_files_for_validation:
                    self.__validate_file(file_path=file)
            else:
                print(f"Directory: {self.__dir_path} does NOT exist!")
                sys.exit(1)
        else:
            print("FILE path or DIRECTORY path has to be given!")
            sys.exit(1)


if __name__ == "__main__":
    JSONDataFilesValidator().main()
