import argparse
import os

from lbaf import PROJECT_PATH
from lbaf.IO.lbsVTDataExtractor import VTDataExtractor
from lbaf.Applications.lbsApplicationBase import ApplicationBase

class PhaseAction(argparse.Action):
    """Custom action to transform phases to list of int(n)|str(x-y)"""
    def __call__(self, parser, namespace, values, option_string=None):
        values_str = values.split(',')
        values = []
        for value_str in values_str:
            if '-' in value_str:
                values.append(value_str)
            else:
                values.append(int(value_str))
        setattr(namespace, self.dest, values)

class VTDataExtractorApplication(ApplicationBase):
    """VTDataExtractor application."""

    def __init__(self):
        super(VTDataExtractorApplication, self).__init__()


    def init_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(allow_abbrev=False)
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
        return parser

    def run(self):
        self.parse_args()
        vtde = VTDataExtractor(input_data_dir=self._args.input_dir,
                            output_data_dir=self._args.output_dir,
                            phases_to_extract=self._args.phases,
                            file_prefix=self._args.file_prefix,
                            file_suffix=self._args.file_suffix,
                            compressed=self._args.compressed,
                            schema_type="LBDatafile",
                            check_schema=False)
        vtde.main()


if __name__ == "__main__":
    VTDataExtractorApplication().run()
