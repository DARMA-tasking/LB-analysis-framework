from schema import Optional, Schema


class SchemaValidator:
    """ Validates schema of VT Object Map files (json)
    """
    def __init__(self):
        self.valid_schema = self._get_valid_schema()

    @staticmethod
    def _get_valid_schema() -> Schema:
        """ Returns representation of a valid schema
        """
        valid_schema = Schema(
            {
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
                                'time': float
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
        return valid_schema

    def is_valid(self, schema_to_validate: dict) -> bool:
        """ Returns True is schema_to_validate is valid with self.valid_schema else False. """
        is_valid = self.valid_schema.is_valid(schema_to_validate)
        return is_valid

    def validate(self, schema_to_validate: dict):
        """ Returns validated schema. """
        return self.valid_schema.validate(schema_to_validate)
