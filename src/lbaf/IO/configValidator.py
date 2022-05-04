from logging import Logger

import yaml
from schema import And, Optional, Or, Schema, Use

from lbaf.Utils.logger import logger


class ConfigValidator:
    """ Validates schema of VT Object Map files (json)
    """
    def __init__(self, config_to_validate: dict, logger: Logger):
        self.__config_to_validate = config_to_validate
        self.__skeleton = Schema({
            Or("from_data", "from_samplers", only_one=True): dict,
            "work_model": {"name": And(str, lambda c: c in ("LoadOnly", "AffineCombination"),
                                       error="LoadOnly or AffineCombination needs to be chosen!"),
                           "parameters": {"alpha": float,
                                          "beta": float,
                                          "gamma": float}},
            "algorithm": {
                "name": And(str, lambda d: d in ("InformAndTransfer", "BruteForce"),
                            error="InformAndTransfer or BruteForce needs to be chosen!"),
                Optional("parameters"): dict
            },
            "exodus": bool,
            "x_procs": int,
            "y_procs": int,
            "z_procs": int,
            "output_file_stem": str,
            Optional("brute_force_optimization"): bool,
            Optional("logging_level"): And(str, Use(str.lower), lambda f: f in ("info", "debug", "warning", "error"),
                                           error="info or debug or warning or error needs to be chosen!"),
            Optional("terminal_background"): And(str, Use(str.lower), lambda g: g in ("light", "dark"),
                                                 error="light or dark needs to be chosen!"),
            Optional("output_dir"): str,
            Optional("generate_multimedia"): bool
        })
        self.__from_data = Schema({"data_stem": str, "phase_id": int})
        self.__from_samplers = Schema({
            "n_objects": int,
            "n_mapped_ranks": int,
            "communication_degree": int,
            "time_sampler": {"name": And(str, Use(str.lower), lambda a: a in ("uniform", "lognormal"),
                                         error="uniform or lognormal needs to be chosen!"),
                             "parameters": [float, float]},
            "volume_sampler": {"name": And(str, Use(str.lower), lambda b: b in ("uniform", "lognormal"),
                                           error="uniform or lognormal needs to be chosen!"),
                               "parameters": [float, float]}
        })
        self.__algorithm = {
            "InformAndTransfer": Schema(
                {"name": "InformAndTransfer",
                 "parameters": {"n_iterations": int, "n_rounds": int, "fanout": int, "order_strategy": And(
                     str, Use(str.lower), lambda e: e in ("arbitrary", "element_id", "increasing_times",
                                                          "decreasing_times", "increasing_connectivity",
                                                          "fewest_migrations", "small_objects"),
                     error="arbitrary or element_id or increasing_times or decreasing_times or increasing_connectivity"
                           " or fewest_migrations or small_objects needs to be chosen!"),
                                "criterion": And(str, lambda f: f in ("Tempered", "StrictLocalizer"),
                                                 error="Tempered or StrictLocalizer needs to be chosen!"),
                                "max_objects_per_transfer": int,
                                "deterministic_transfer": bool}}),
            "BruteForce": Schema(
                {"name": "BruteForce",
                 Optional("parameters"): {"skip_transfer": bool}})
        }
        self.__logger = logger

    @staticmethod
    def is_valid(valid_schema: Schema, schema_to_validate: dict) -> bool:
        """ Returns True is schema_to_validate is valid with self.valid_schema else False. """
        is_valid = valid_schema.is_valid(schema_to_validate)
        return is_valid

    @staticmethod
    def validate(valid_schema: Schema, schema_to_validate: dict):
        """ Returns validated schema. """
        return valid_schema.validate(schema_to_validate)

    def main(self):
        """ Main routine for the config validation. """
        # Validate Skeleton
        if self.is_valid(valid_schema=self.__skeleton, schema_to_validate=self.__config_to_validate):
            self.__logger.info("Skeleton schema is VALID!")
        else:
            self.__logger.error("Skeleton schema is INVALID!")
            self.validate(valid_schema=self.__skeleton, schema_to_validate=self.__config_to_validate)

        # Validate from_data/from_samplers
        if (from_data := self.__config_to_validate.get("from_data")) is not None:
            self.__logger.info("Reading from data was chosen.")
            if self.is_valid(valid_schema=self.__from_data, schema_to_validate=from_data):
                self.__logger.info("from_data schema is VALID!")
            else:
                self.__logger.error("from_data schema is INVALID!")
                self.validate(valid_schema=self.__from_data, schema_to_validate=from_data)
        elif (from_samplers := self.__config_to_validate.get("from_samplers")) is not None:
            self.__logger.info("Simulate from samplers was chosen.")
            if self.is_valid(valid_schema=self.__from_samplers, schema_to_validate=from_samplers):
                self.__logger.info("from_samplers schema is VALID!")
            else:
                self.__logger.error("from_samplers schema is INVALID!")
                self.validate(valid_schema=self.__from_samplers, schema_to_validate=from_samplers)

        # Validate Algorithm
        if (algorithm := self.__config_to_validate.get("algorithm").get("name")) is not None:
            self.__logger.info(f"Checking algorithm: {algorithm}")
            if self.is_valid(valid_schema=self.__algorithm.get(algorithm),
                             schema_to_validate=self.__config_to_validate.get("algorithm")):
                self.__logger.info(f"Algorithm: {algorithm} schema is VALID!")
            else:
                self.__logger.error("Algorithm: {algorithm} schema is INVALID!")
                self.validate(valid_schema=self.__algorithm.get(algorithm),
                              schema_to_validate=self.__config_to_validate.get("algorithm"))


if __name__ == "__main__":
    with open("../Applications/conf.yaml", "rt") as config_file:
        yaml_str = config_file.read()
        configuration = yaml.safe_load(yaml_str)

    ConfigValidator(config_to_validate=configuration, logger=logger()).main()
