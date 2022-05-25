import os
import sys

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

import brotli
import json

from ..IO.schemaValidator import SchemaValidator


class VTDataExtractor:
    """ Reads VT data and saves chosen phases from it. """
    def __init__(self, input_data_dir: str, output_data_dir: str, phases_to_extract: list, file_prefix: str = "data",
                 file_suffix: str = "json", compressed: bool = True):
        self.input_data_dir = input_data_dir
        self.output_data_dir = os.path.join(project_path, output_data_dir)
        self.phases_to_extract = self._process_input_phases(phases_to_extract=phases_to_extract)
        self.file_prefix = file_prefix
        self.file_suffix = file_suffix
        self.compressed = compressed
        self._initial_checks()
        self._get_files_list()

    def _initial_checks(self):
        """ Checks if data and directories exists. """
        # Input data
        if os.path.isdir(os.path.abspath(self.input_data_dir)):
            self.input_data_dir = os.path.abspath(self.input_data_dir)
            print(f"Input data directory: {self.input_data_dir}")
        elif os.path.isdir(os.path.join(project_path, self.input_data_dir)):
            self.input_data_dir = os.path.join(project_path, self.input_data_dir)
            print(f"Input data directory: {self.input_data_dir}")
        else:
            print("Input data directory NOT FOUND!")
            raise SystemExit(1)
        # Output data
        if not os.path.exists(self.output_data_dir):
            print("Output data directory not found, CREATING ...")
            os.makedirs(self.output_data_dir)

    @staticmethod
    def _process_input_phases(phases_to_extract: list) -> list:
        """ Creates a list of integers, based on input phases_to_extract. """
        processed_list = []
        for phase in phases_to_extract:
            if isinstance(phase, int):
                processed_list.append(phase)
            elif isinstance(phase, str):
                phase_list = phase.split('-')
                if int(phase_list[0]) >= int(phase_list[1]):
                    print('Phase range wrongly declared!')
                    raise SystemExit(1)
                phase_range = list(range(int(phase_list[0]), int(phase_list[1]) + 1))
                processed_list.extend(phase_range)
        processed_set = set(processed_list)
        processed_list = list(processed_set)
        processed_list.sort()

        return processed_list

    def _get_files_list(self) -> list:
        """ Returns list of files to iterate over and read data from them. """
        files = [os.path.abspath(os.path.join(self.input_data_dir, file)) for file in os.listdir(self.input_data_dir)
                 if file.startswith(self.file_prefix) and file.endswith(self.file_suffix)]
        try:
            files.sort(key=lambda x: int(x.split('.')[1]))
        except ValueError as err:
            print(f"Values in filenames can not be converted to `int`!\nPhases are not sorted.\nERROR: {err}")

        return files

    @staticmethod
    def get_data_from_file(file_path: str) -> dict:
        """ Returns data from given file_path. """
        with open(file_path, "rb") as compr_json_file:
            compr_bytes = compr_json_file.read()
            try:
                decompr_bytes = brotli.decompress(compr_bytes)
                decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
            except brotli.error:
                decompressed_dict = json.loads(compr_bytes.decode("utf-8"))

        # Validate schema
        if SchemaValidator().is_valid(schema_to_validate=decompressed_dict):
            print(f"Valid JSON schema in {file_path}")
        else:
            print(f"Invalid JSON schema in {file_path}")
            SchemaValidator().validate(schema_to_validate=decompressed_dict)
            raise SystemExit(1)

        return decompressed_dict

    @staticmethod
    def get_extracted_phases(data: dict, phases_to_extract: list) -> dict:
        """ Returns just wanted phases from given data and list of phases to extract. """
        extracted_phases = {"phases": []}
        for phase_number, phase in enumerate(data["phases"]):
            if phase_number in phases_to_extract:
                extracted_phases["phases"].append(phase)

        return extracted_phases

    @staticmethod
    def save_extracted_phases(extracted_phases: dict, file_path: str, compressed: bool = True) -> None:
        """ Saves extracted data with or without compression. """
        json_str = json.dumps(extracted_phases, separators=(",", ":"))
        if compressed:
            saved_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
        else:
            saved_str = json_str

        print(f"Saving file: {file_path}")
        with open(file_path, "wb") as compr_json_file:
            compr_json_file.write(saved_str)

    def main(self):
        files = self._get_files_list()
        for file in files:
            print(f"Processing file: {file}")
            file_path = os.path.join(self.output_data_dir, file.split(os.sep)[-1])
            data = self.get_data_from_file(file_path=file)
            extracted_phases = self.get_extracted_phases(data=data, phases_to_extract=self.phases_to_extract)
            self.save_extracted_phases(extracted_phases=extracted_phases, file_path=file_path,
                                       compressed=self.compressed)
        print("=====> DONE <=====")


if __name__ == '__main__':
    # Here phases are declared
    # It should be declared as list of [int or str]
    # Int is just a phase number/id
    # Str is a range of pages in form of "a-b", "a" must be smaller than "b", e.g. "9-11" => [9, 10, 11] will be added
    phases = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, "9-11"]
    vtde = VTDataExtractor(input_data_dir="data/nolb-8color-16nodes-data", output_data_dir="output",
                           phases_to_extract=phases)
    vtde.main()
