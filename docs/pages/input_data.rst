Input data
==========

`LBAF_app.py` supports two kind on input data.

LB data
-------

.. code-block:: python

  Schema(
            {
                'type': And(str, lambda a: a in ("LBDatafile", "LBStatsfile"),
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

LB stats
--------

.. code-block:: python

  Schema(
            {
                'type': And(str, lambda a: a in ("LBDatafile", "LBStatsfile"),
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
