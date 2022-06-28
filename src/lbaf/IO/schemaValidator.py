from collections import Iterable
import sys

from schema import And, Optional, Schema
from ..Utils.exception_handler import exc_handler


class SchemaValidator:
    """ Validates schema of VT Object Map files (json)
    """
    def __init__(self, schema_type: str):
        self.schema_type = schema_type
        self.valid_schema = self._get_valid_schema()

    @staticmethod
    def get_error_message(iterable_collection: Iterable) -> str:
        """ Return error message. """
        return " or ".join(iterable_collection)

    def _get_valid_schema(self) -> Schema:
        """ Returns representation of a valid schema
        """
        allowed_types = ("LBDatafile", "LBStatsfile")
        valid_schema_data = Schema(
            {
                'type': And(str, lambda a: a in allowed_types,
                            error=f"{self.get_error_message(allowed_types)} must be chosen"),
                'phases': [
                    {
                        'id': int,
                        'tasks': [
                            {
                                'entity': {
                                    Optional('collection_id'): int,
                                    'home': int,
                                    'id': int,
                                    Optional('index'): [int],
                                    'type': str,
                                    'migratable': bool,
                                    Optional('objgroup_id'): int
                                },
                                'node': int,
                                'resource': str,
                                Optional('subphases'): [
                                    {
                                        'id': int,
                                        'time': float,
                                    }
                                ],
                                'time': float,
                                Optional('user_defined'): dict
                            },
                        ],
                        Optional('communications'): [
                            {
                                'type': str,
                                'to': {
                                    'type': str,
                                    'id': int,
                                    Optional('home'): int,
                                    Optional('collection_id'): int,
                                    Optional('migratable'): bool,
                                    Optional('index'): [int],
                                    Optional('objgroup_id'): int,
                                },
                                'messages': int,
                                'from': {
                                    'type': str,
                                    'id': int,
                                    Optional('home'): int,
                                    Optional('collection_id'): int,
                                    Optional('migratable'): bool,
                                    Optional('index'): [int],
                                    Optional('objgroup_id'): int,
                                },
                                'bytes': float
                            }
                        ]
                    },
                ]
            }
        )
        valid_schema_stats = Schema(
            {
                'type': And(str, lambda a: a in allowed_types,
                            error=f"{self.get_error_message(allowed_types)} must be chosen"),
                'phases': [
                    {
                        "id": int,
                        Optional("migration count"): int,
                        Optional("post-LB"): {
                            "Object_comm": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Object_load_modeled": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Object_load_raw": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Rank_comm": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Rank_load_modeled": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Rank_load_raw": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            }
                        },
                        "pre-LB": {
                            "Object_comm": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Object_load_modeled": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Object_load_raw": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Rank_comm": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Rank_load_modeled": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            },
                            "Rank_load_raw": {
                                "avg": float,
                                "car": float,
                                "imb": float,
                                "kur": float,
                                "max": float,
                                "min": float,
                                "npr": float,
                                "skw": float,
                                "std": float,
                                "sum": float,
                                "var": float
                            }
                        }
                    },
                ]
            }
        )

        if self.schema_type == "LBDatafile":
            return valid_schema_data
        elif self.schema_type == "LBStatsfile":
            return valid_schema_stats

        sys.excepthook = exc_handler
        raise TypeError(f"Unsupported schema type: {self.schema_type} was given")

    def is_valid(self, schema_to_validate: dict) -> bool:
        """ Returns True if schema_to_validate is valid with self.valid_schema else False. """
        is_valid = self.valid_schema.is_valid(schema_to_validate)
        return is_valid

    def validate(self, schema_to_validate: dict):
        """ Return validated schema. """

        def exception_handler(exception_type, exception, traceback):
            """ Exception handler for hiding traceback. """
            self.__logger.error(f"{exception_type.__name__} {exception}")

        sys.excepthook = exception_handler
        return self.valid_schema.validate(schema_to_validate)
