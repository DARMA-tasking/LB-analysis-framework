from collections import Iterable
from logging import Logger

from schema import And, Optional, Or, Schema, Use


# Allowed configuration values
ALLOWED_STRATEGIES = ("arbitrary", "element_id", "increasing_times", "decreasing_times", "increasing_connectivity",
                      "fewest_migrations", "small_objects")
ALLOWED_WORK_MODELS = ("LoadOnly", "AffineCombination")
ALLOWED_ALGORITHMS = ("InformAndTransfer", "BruteForce")
ALLOWED_CRITERIA = ("Tempered", "StrictLocalizer")
ALLOWED_LOGGING_LEVELS = ("info", "debug", "warning", "error")
ALLOWED_TIME_VOLUME_SAMPLER = ("uniform", "lognormal")
ALLOWED_TERMINAL_BACKGROUND = ("light", "dark")


def get_error_msg(iterable_collection: Iterable) -> str:
    """ Return error message. """
    return " or ".join(iterable_collection)


class ConfigurationValidator:
    """ Validate data in an YAML configuration file.
    """
    def __init__(self, config_to_validate: dict, logger: Logger):
        self.__config_to_validate = config_to_validate
        self.__skeleton = Schema({
            Or("from_data", "from_samplers", only_one=True): dict,
            "work_model": {"name": And(str, lambda c: c in ALLOWED_WORK_MODELS,
                                       error=f"{get_error_msg(ALLOWED_WORK_MODELS)} needs to be chosen"),
                           "parameters": {"alpha": float,
                                          "beta": float,
                                          "gamma": float}},
            "algorithm": {
                "name": And(str, lambda d: d in ALLOWED_ALGORITHMS,
                            error=f"{get_error_msg(ALLOWED_ALGORITHMS)} needs to be chosen"),
                Optional("parameters"): dict
            },
            "output_file_stem": str,
            Optional("exodus"): {"x_procs": int, "y_procs": int, "z_procs": int},
            Optional("brute_force_optimization"): bool,
            Optional("logging_level"): And(str, Use(str.lower), lambda f: f in ALLOWED_LOGGING_LEVELS,
                                           error=f"{get_error_msg(ALLOWED_LOGGING_LEVELS)} needs to be chosen"),
            Optional("terminal_background"): And(str, Use(str.lower), lambda g: g in ALLOWED_TERMINAL_BACKGROUND,
                                                 error=f"{get_error_msg(ALLOWED_TERMINAL_BACKGROUND)} needs to be "
                                                       f"chosen"),
            Optional("output_dir"): str,
            Optional("generate_multimedia"): bool
        })
        self.__from_data = Schema({"data_stem": str, "phase_id": int})
        self.__from_samplers = Schema({
            "n_objects": int,
            "n_mapped_ranks": int,
            "communication_degree": int,
            "time_sampler": {"name": And(str, Use(str.lower), lambda a: a in ALLOWED_TIME_VOLUME_SAMPLER,
                                         error=f"{get_error_msg(ALLOWED_TIME_VOLUME_SAMPLER)} needs to be chosen"),
                             "parameters": And([float], lambda s: len(s) == 2,
                                               error="There should be exactly 2 parameters provided")},
            "volume_sampler": {"name": And(str, Use(str.lower), lambda b: b in ALLOWED_TIME_VOLUME_SAMPLER,
                                           error=f"{get_error_msg(ALLOWED_TIME_VOLUME_SAMPLER)} needs to be chosen"),
                               "parameters": And([float], lambda s: len(s) == 2,
                                                 error="There should be exactly 2 parameters provided")}
        })
        self.__algorithm = {
            "InformAndTransfer": Schema(
                {"name": "InformAndTransfer",
                 "parameters": {"n_iterations": int,
                                "n_rounds": int,
                                "fanout": int,
                                "order_strategy": And(str, Use(str.lower),
                                                      lambda e: e in ALLOWED_STRATEGIES,
                                                      error=f"{get_error_msg(ALLOWED_STRATEGIES)} needs to be chosen"),
                                "criterion": And(str, lambda f: f in ALLOWED_CRITERIA,
                                                 error=f"{get_error_msg(ALLOWED_CRITERIA)} needs to be chosen"),
                                "max_objects_per_transfer": int,
                                "deterministic_transfer": bool}}),
            "BruteForce": Schema(
                {"name": "BruteForce",
                 Optional("parameters"): {"skip_transfer": bool}})
        }
        self.__logger = logger

    @staticmethod
    def is_valid(valid_schema: Schema, schema_to_validate: dict) -> bool:
        """ Return True if schema_to_validate is valid with valid_schema else False. """
        is_valid = valid_schema.is_valid(schema_to_validate)
        return is_valid

    @staticmethod
    def validate(valid_schema: Schema, schema_to_validate: dict):
        """ Return validated schema. """
        return valid_schema.validate(schema_to_validate)

    def main(self):
        """ Main routine for the config validation. """
        # Validate skeleton
        if self.is_valid(valid_schema=self.__skeleton, schema_to_validate=self.__config_to_validate):
            self.__logger.info("Skeleton schema is valid")
        else:
            self.__logger.error("Skeleton schema is invalid")
            self.validate(valid_schema=self.__skeleton, schema_to_validate=self.__config_to_validate)

        # Validate from_data/from_samplers
        if (from_data := self.__config_to_validate.get("from_data")) is not None:
            self.__logger.info("Reading from data was chosen.")
            if self.is_valid(valid_schema=self.__from_data, schema_to_validate=from_data):
                self.__logger.info("from_data schema is valid")
            else:
                self.__logger.error("from_data schema is invalid")
                self.validate(valid_schema=self.__from_data, schema_to_validate=from_data)
        elif (from_samplers := self.__config_to_validate.get("from_samplers")) is not None:
            self.__logger.info("Simulate from samplers was chosen.")
            if self.is_valid(valid_schema=self.__from_samplers, schema_to_validate=from_samplers):
                self.__logger.info("from_samplers schema is valid")
            else:
                self.__logger.error("from_samplers schema is invalid")
                self.validate(valid_schema=self.__from_samplers, schema_to_validate=from_samplers)

        # Validate algorithm
        if (algorithm := self.__config_to_validate.get("algorithm").get("name")) is not None:
            self.__logger.info(f"Checking algorithm schema of: {algorithm}")
            if self.is_valid(valid_schema=self.__algorithm.get(algorithm),
                             schema_to_validate=self.__config_to_validate.get("algorithm")):
                self.__logger.info(f"Algorithm: {algorithm} schema is valid")
            else:
                self.__logger.error("Algorithm: {algorithm} schema is invalid")
                self.validate(valid_schema=self.__algorithm.get(algorithm),
                              schema_to_validate=self.__config_to_validate.get("algorithm"))
