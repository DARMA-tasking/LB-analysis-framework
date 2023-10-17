"""Configuration Updater"""
import os
import sys
import yaml
import importlib

if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH, __version__
from lbaf.IO.lbsConfigurationValidator import ConfigurationValidator
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
from lbaf.Utils.lbsPath import abspath
from lbaf.Utils.lbsLogging import Logger, get_logger


class ConfigUpdater:

    def __init__(self):
        self.__args: Optional[dict] = None
        self.__logger = get_logger()

    def __validate_configuration(self, config: dict):
        """Configuration file validation."""
        ConfigurationValidator(
            config_to_validate=config, logger=self.__logger).main()

    def __parse_args(self):
        """Parse arguments."""
        parser = PromptArgumentParser(
            allow_abbrev=False,
            description="Update configuration files with new visualization parameters",
            prompt_default=False)
        parser.add_argument(
            "-d", "--directory",
            help="Path to a directory containing config files to be updated. If path is relative it must be resolvable from either the current working directory or the config directory",
            default=""),
        parser.add_argument(
            "-f", "--filepath",
            help="Path to a single config file to be updated. If path is relative it must be resolvable from either the current working directory or the config directory.",
            default=""),
        parser.add_argument(
            "-o", "--output",
            help="Path to directory where new config files should be saved. If path is relative it must be resolvable from either the current working directory or the config directory.",
            default="updated-config"
        )
        self.__args = parser.parse_args()


    def __read_configuration_file(self, config_path):
        try:
            with open(config_path, "r") as file:
                config_dict = yaml.safe_load(file)
            return config_dict
        except FileNotFoundError:
            self.__logger.error(f"File not found: {config_path}")
        except yaml.YAMLError as e:
            self.__logger.error(f"Error parsing YAML in {config_path}: {e}")
        return None  # Return None in case of errors

    def __update_conf(self, config: dict):

        if "output_dir" in config:
            output_dir = config["output_dir"]

            if "output_file_stem" in config:
                file_stem = config["output_file_stem"]

                if "LBAF_Viz" in config:
                    config["visualization"] = config.pop("LBAF_Viz")
                    config["visualization"]["output_visualization_dir"] = output_dir
                    config["visualization"]["output_visualization_file_stem"] = file_stem

        return config

    def __write_config(self, config: dict, output_dir: str, filename: str):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file_path = os.path.join(output_dir, filename)

        with open(output_file_path, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

        self.__logger.info(f"New configuration file written to {output_file_path}")

    def initialize(self):

        # Parse command line arguments
        self.__parse_args()

        directory = str(self.__args.directory)
        filepath = str(self.__args.filepath)

        if directory:
            # Check if the directory path is valid
            if os.path.exists(directory) and os.path.isdir(directory):
                # Find all files in the directory that end with ".yaml"
                config_files = [f for f in os.listdir(directory) if f.endswith(".yaml")]
                for config_file in config_files:
                    full_path = directory + "/" + config_file
                    self.run(full_path)
            else:
                self.__logger.error(f"The directory path {directory} is invalid.")

        if filepath:
            self.run(filepath)

        return

    def run(self, filepath: str):
        output_dir = str(self.__args.output)
        filename = os.path.basename(filepath)

        if not os.path.exists(filepath):
            self.__logger.error(f"File not found: {filepath}")
            return

        config = self.__read_configuration_file(filepath)

        if config is None:
            self.__logger.error(f"Could not find configuration file at {filepath}")
            return

        self.__logger.info(f"Updating {filename}")

        new_config = self.__update_conf(config)
        self.__validate_configuration(new_config)
        self.__write_config(new_config, output_dir, filename)

if __name__ == "__main__":
    ConfigUpdater().initialize()
