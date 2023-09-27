import argparse
import importlib
import json
import os
import sys
import time
from multiprocessing import get_context
from multiprocessing.pool import Pool
from typing import Optional

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsLogging import get_logger, Logger
# pylint:disable=C0413:wrong-import-position

try:
    import brotli
    BROTLI_NOT_IMPORTED = False
except ImportError as e:
    print(f"Brotli was not imported: {e}")
    BROTLI_NOT_IMPORTED = True


class VTDataExtractor():
    """Reads VT data and saves chosen phases from it. """

    def __init__(self, input_data_dir: str, output_data_dir: str, phases_to_extract: list, file_prefix: str = "stats",
                 file_suffix: str = "json", compressed: bool = True, schema_type: str = "LBDatafile",
                 check_schema: bool = False, logger: Optional[Logger] = None):
        self.__logger = logger if logger is not None else get_logger()
        self.start_t = time.perf_counter()
        self.input_data_dir = input_data_dir
        self.output_data_dir = os.path.join(PROJECT_PATH, output_data_dir)
        self.phases_to_extract = self._process_input_phases(phases_to_extract=phases_to_extract)
        self.file_prefix = file_prefix
        self.file_suffix = file_suffix
        self.compressed = compressed
        self.schema_type = schema_type
        self.check_schema = check_schema
        self._initial_checks()
        self._get_files_list()

    def _initial_checks(self):
        """Checks if data and directories exists."""
        print(f"Looking for files with prefix: {self.file_prefix}")
        print(f"Looking for files with suffix: {self.file_suffix}")
        print(f"Phases to extract: {self.phases_to_extract}")
        # Input data
        if os.path.isdir(os.path.abspath(self.input_data_dir)):
            self.input_data_dir = os.path.abspath(self.input_data_dir)
            print(f"Input data directory: {self.input_data_dir}")
        elif os.path.isdir(os.path.join(PROJECT_PATH, self.input_data_dir)):
            self.input_data_dir = os.path.join(PROJECT_PATH, self.input_data_dir)
            print(f"Input data directory: {self.input_data_dir}")
        else:
            self.__logger.error("Input data directory not found.")
            raise SystemExit(1)
        # Output data
        if not os.path.exists(self.output_data_dir):
            print("Output data directory not found, creating ...")
            os.makedirs(self.output_data_dir)

    @staticmethod
    def _process_input_phases(phases_to_extract: list) -> list:
        """Creates a list of integers, based on input phases_to_extract."""
        processed_list = []
        for phase in phases_to_extract:
            if isinstance(phase, int):
                processed_list.append(phase)
            elif isinstance(phase, str):
                phase_list = phase.split('-')
                if int(phase_list[0]) >= int(phase_list[1]):
                    get_logger().error("Phase range wrongly declared.")
                    raise SystemExit(1)
                phase_range = list(range(int(phase_list[0]), int(phase_list[1]) + 1))
                processed_list.extend(phase_range)
        processed_set = set(processed_list)
        processed_list = list(processed_set)
        processed_list.sort()

        return processed_list

    def _get_files_list(self) -> list:
        """Returns list of files to iterate over and read data from them."""
        files = [os.path.abspath(os.path.join(self.input_data_dir, file)) for file in os.listdir(self.input_data_dir)
                 if file.startswith(self.file_prefix) and file.endswith(self.file_suffix)]
        if not files:
            self.__logger.error("No files were found")
            raise SystemExit(1)
        try:
            files.sort(key=lambda x: int(x.split('.')[1]))
        except ValueError as err:
            self.__logger.error(f"Values in filenames can not be converted to `int`.\nPhases are not sorted.\n"
                                f"ERROR: {err}")
            raise SystemExit(1) from err

        return files

    def _get_data_from_file(self, file_path: str) -> dict:
        """Returns data from given file_path."""
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
                with open(file_path, "rt", encoding="utf-8") as uncompr_json_file:
                    uncompr_str = uncompr_json_file.read()
                    decompressed_dict = json.loads(uncompr_str)
            except UnicodeDecodeError as err:
                raise Exception(
                    "\n============================================================\n"
                    "\t\tCan not read compressed data without Brotli."
                    "\n============================================================") from err

        if decompressed_dict.get("type") not in ("LBDatafile", "LBStatsfile"):
            decompressed_dict["type"] = self.schema_type
        else:
            self.schema_type = decompressed_dict.get("type")

        if self.check_schema:
            try:
                from lbaf.imported.JSON_data_files_validator import \
                    SchemaValidator  # pylint:disable=C0415:import-outside-toplevel
            except ModuleNotFoundError as err:
                raise ModuleNotFoundError(
                    "\n====================================================================\n"
                    "\t\tCan not check schema without schema module imported."
                    "\n====================================================================") from err
            # Validate schema
            if SchemaValidator(schema_type=self.schema_type).is_valid(schema_to_validate=decompressed_dict):
                print(f"Valid JSON schema in {file_path}")
            else:
                self.__logger.error(
                    f"Invalid JSON schema in {file_path}")
                raise SystemExit(1)

        return decompressed_dict

    @staticmethod
    def _get_extracted_phases(data: dict, phases_to_extract: list) -> dict:
        """Returns just wanted phases from given data and list of phases to extract."""
        extracted_phases = {"phases": []}
        for phase_number, phase in enumerate(data["phases"]):
            if phase_number in phases_to_extract:
                extracted_phases["phases"].append(phase)

        return extracted_phases

    def _save_extracted_phases(self, extracted_phases: dict, file_path: str) -> None:
        """Saves extracted data with or without compression."""
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
            with open(file_path, "wt", encoding="utf-8") as compr_json_file:
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
        """Execute the data extraction."""
        files = self._get_files_list()
        with Pool(context=get_context("fork")) as pool:
            results = pool.imap_unordered(self._extraction, files)
            for filename, duration in results:
                print(f"===> File: {filename} completed in {duration:.2f}s")

        end_t = time.perf_counter()
        total_duration = end_t - self.start_t
        print(f"=====> DONE in {total_duration:.2f} <=====")


class PhaseAction(argparse.Action):
    """Custom action to split phases string argument to a list of int(n)|str(x-y)"""

    def __call__(self, parser, namespace, values, option_string=None):
        values_str = values.split(',')
        values = []
        for value_str in values_str:
            if '-' in value_str:
                values.append(value_str)
            else:
                values.append(int(value_str))
        setattr(namespace, self.dest, values)


class VTDataExtractorRunner:
    """VTDataExtractor application."""

    def __init__(self):
        self.__args: dict = None

    def __parse_args(self):
        """Parse arguments."""
        parser = PromptArgumentParser(allow_abbrev=False,
                                      description="Reads VT data and saves chosen phases from it.",
                                      prompt_default=True)
        parser.add_argument("--input-dir", help="Input data directory", required=True)
        parser.add_argument("--output-dir", help="Output data directory",
                            default=os.path.join(PROJECT_PATH, "output", "extract"))
        parser.add_argument("--phases",
                            help="Phase numbers or ranges separated by a comma."
                            "Example: 1-6,8,10 will extract phases from 1 to 6, phase 8 and phase 10",
                            default=None,
                            required=True,
                            action=PhaseAction
                            )
        parser.add_argument("--file-prefix", help="File prefix", default="data")
        parser.add_argument("--file-suffix", help="File suffix", default="json")
        parser.add_argument("--compressed", help="To compress output data using brotli", default=False, type=bool)
        self.__args = parser.parse_args()

    def run(self):
        """Run the VTDataExtractor"""
        # Parse command line arguments
        self.__parse_args()

        vtde = VTDataExtractor(input_data_dir=self.__args.input_dir,
                               output_data_dir=self.__args.output_dir,
                               phases_to_extract=self.__args.phases,
                               file_prefix=self.__args.file_prefix,
                               file_suffix=self.__args.file_suffix,
                               compressed=self.__args.compressed,
                               schema_type="LBDatafile",
                               check_schema=False)
        vtde.main()


if __name__ == "__main__":
    VTDataExtractorRunner().run()
