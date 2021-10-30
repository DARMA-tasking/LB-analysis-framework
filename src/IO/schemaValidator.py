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
                                    Optional('home'): int,
                                    'id': int,
                                    Optional('index'): [int],
                                    'type': str
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
                                    Optional('home'): int
                                },
                                'messages': int,
                                'from': {
                                    'type': str,
                                    'id': int,
                                    Optional('home'): int
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
        """ Returns True is schema_to_validate is valid with self.valid_schema else False
        """
        is_valid = self.valid_schema.is_valid(schema_to_validate)
        return is_valid
