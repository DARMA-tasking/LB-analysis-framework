import os
import sys

try:
    project_path = f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3])
    print(f"Started in directory: {project_path}")
    sys.path.append(project_path)
except Exception as e:
    print(f"Can not add project path to system path! Exiting!\nERROR: {e}")
    raise SystemExit(1)

from multiprocessing import Pool
import time

import json

from lbaf.Utils.exception_handler import exc_handler

try:
    import brotli
    BROTLI_NOT_IMPORTED = False
except ImportError as e:
    print(f'Brotli was not imported: {e}')
    BROTLI_NOT_IMPORTED = True


class VTDataExtractor:
    """ Reads VT data and saves chosen phases from it. """
    def __init__(self, input_data_dir: str, output_data_dir: str, phases_to_extract: list, file_prefix: str = "stats",
                 file_suffix: str = "json", compressed: bool = True, schema_type: str = "LBDatafile",
                 check_schema: bool = False):
        self.start_t = time.perf_counter()
        self.input_data_dir = input_data_dir
        self.output_data_dir = os.path.join(project_path, output_data_dir)
        self.phases_to_extract = self._process_input_phases(phases_to_extract=phases_to_extract)
        self.file_prefix = file_prefix
        self.file_suffix = file_suffix
        self.compressed = compressed
        self.schema_type = schema_type
        self.check_schema = check_schema
        self._initial_checks()
        self._get_files_list()

    def _initial_checks(self):
        """ Checks if data and directories exists. """
        print(f"Looking for files with prefix: {self.file_prefix}")
        print(f"Looking for files with suffix: {self.file_suffix}")
        print(f"Phases to extract: {self.phases_to_extract}")
        # Input data
        if os.path.isdir(os.path.abspath(self.input_data_dir)):
            self.input_data_dir = os.path.abspath(self.input_data_dir)
            print(f"Input data directory: {self.input_data_dir}")
        elif os.path.isdir(os.path.join(project_path, self.input_data_dir)):
            self.input_data_dir = os.path.join(project_path, self.input_data_dir)
            print(f"Input data directory: {self.input_data_dir}")
        else:
            sys.excepthook = exc_handler
            raise SystemExit("Input data directory NOT FOUND!")
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
                    print("Phase range wrongly declared!")
                    sys.excepthook = exc_handler
                    raise SystemExit("Phase range wrongly declared!")
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
        if not files:
            sys.excepthook = exc_handler
            raise SystemExit("No files were found")
        try:
            files.sort(key=lambda x: int(x.split('.')[1]))
        except ValueError as err:
            sys.excepthook = exc_handler
            raise ValueError(f"Values in filenames can not be converted to `int`!\nPhases are not sorted.\n"
                             f"ERROR: {err}")

        return files

    def _get_data_from_file(self, file_path: str) -> dict:
        """ Returns data from given file_path. """
        if not BROTLI_NOT_IMPORTED:
            with open(file_path, "rb") as compr_json_file:
                compr_bytes = compr_json_file.read()
                try:
                    decompr_bytes = brotli.decompress(compr_bytes)
                    decompressed_dict = json.loads(decompr_bytes.decode("utf-8"))
                except brotli.error:
                    decompressed_dict = json.loads(compr_bytes.decode("utf-8"))
        else:
            try:
                with open(file_path, "rt") as uncompr_json_file:
                    uncompr_str = uncompr_json_file.read()
                    decompressed_dict = json.loads(uncompr_str)
            except UnicodeDecodeError as err:
                sys.excepthook = exc_handler
                raise Exception("\n============================================================\n"
                                "\t\tCan not read compressed data without Brotli."
                                "\n============================================================")

        if decompressed_dict.get("type") not in ("LBDatafile", "LBStatsfile"):
            decompressed_dict["type"] = self.schema_type
        else:
            self.schema_type = decompressed_dict.get("type")

        if self.check_schema:
            try:
                from lbaf.IO.schemaValidator import SchemaValidator
            except ModuleNotFoundError as err:
                sys.excepthook = exc_handler
                raise ModuleNotFoundError("\n====================================================================\n"
                                          "\t\tCan not check schema without schema module imported."
                                          "\n====================================================================")
            # Validate schema
            if SchemaValidator(schema_type=self.schema_type).is_valid(schema_to_validate=decompressed_dict):
                print(f"Valid JSON schema in {file_path}")
            else:
                print(f"Invalid JSON schema in {file_path}")
                SchemaValidator(schema_type=self.schema_type).validate(schema_to_validate=decompressed_dict)
                sys.excepthook = exc_handler
                raise SystemExit(1)

        return decompressed_dict

    @staticmethod
    def _get_extracted_phases(data: dict, phases_to_extract: list) -> dict:
        """ Returns just wanted phases from given data and list of phases to extract. """
        extracted_phases = {"phases": []}
        for phase_number, phase in enumerate(data["phases"]):
            if phase_number in phases_to_extract:
                extracted_phases["phases"].append(phase)

        return extracted_phases

    def _save_extracted_phases(self, extracted_phases: dict, file_path: str) -> None:
        """ Saves extracted data with or without compression. """
        if extracted_phases.get("type") is None:
            extracted_phases["type"] = self.schema_type
        json_str = json.dumps(extracted_phases, separators=(",", ":"))
        if self.compressed and not BROTLI_NOT_IMPORTED:
            saved_str = brotli.compress(string=json_str.encode("utf-8"), mode=brotli.MODE_TEXT)
            print(f"==> Saving file: {file_path}")
            with open(file_path, "wb") as compr_json_file:
                compr_json_file.write(saved_str)
        else:
            saved_str = json_str
            with open(file_path, "wt") as compr_json_file:
                compr_json_file.write(saved_str)

    def _extraction(self, file: str) -> tuple:
        start_t = time.perf_counter()
        print(f"=> Processing file: {file}")
        file_path = os.path.join(self.output_data_dir, file.split(os.sep)[-1])
        data = self._get_data_from_file(file_path=file)
        extracted_phases = self._get_extracted_phases(data=data, phases_to_extract=self.phases_to_extract)
        self._save_extracted_phases(extracted_phases=extracted_phases, file_path=file_path)
        end_t = time.perf_counter()
        return file, end_t - start_t

    def main(self):
        files = self._get_files_list()
        with Pool() as pool:
            results = pool.imap_unordered(self._extraction, files)
            for filename, duration in results:
                print(f"===> File: {filename} completed in {duration:.2f}s")

        end_t = time.perf_counter()
        total_duration = end_t - self.start_t
        print(f"=====> DONE in {total_duration:.2f} <=====")


if __name__ == '__main__':
    # Here phases are declared
    # It should be declared as list of [int or str]
    # Int is just a phase number/id e.g. [1, 2, 3, 4]
    # Str is a range of pages in form of "a-b", "a" must be smaller than "b", e.g. "9-11" => [9, 10, 11] will be added
    phases = [0, 1, 2, 3, "4-9"]
    vtde = VTDataExtractor(input_data_dir="../data/test_data",
                           output_data_dir="../output",
                           phases_to_extract=phases,
                           file_prefix="stats",
                           file_suffix="json",
                           compressed=False,
                           schema_type="LBDatafile",
                           check_schema=False)
    vtde.main()
