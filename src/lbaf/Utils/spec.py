spec = PhaseSpecification({
    "tasks": [
        TaskSpecification({
            "collection_id": 0,
            "time": 2.0
        }),
        TaskSpecification({
            "collection_id": 0,
            "time": 3.5
        }),
        TaskSpecification({
            "collection_id": 0,
            "time": 5.0
        })
    ],
    "communications": [
        CommunicationSpecification({
            "size": 10000.0,  # c1 (size)
            "from": 0,  # from t1
            "to": 2  # to t3
        }),
        CommunicationSpecification({
            "size": 15000.0,  # c2 (size)
            "from": 1,  # from t2
            "to": 2  # to t3
        }),
        CommunicationSpecification({
            "size": 20000.0,  # c3 (size)
            "from": 2,  # from t3
            "to": 1  # to t2
        })
    ],
    "shared_blocks": [
        # S1
        SharedBlockSpecification({
            "size": 10000.0,
            "home_rank": 0,
            "tasks": {0, 1}
        }),
        # S2
        SharedBlockSpecification({
            "size": 15000.0,
            "home_rank": 1,
            "tasks": {2}
        })
    ],
    "ranks": {
        0: RankSpecification({"tasks": {0, 1}}),
        1: RankSpecification({"tasks": {2}})
    }
})

spec["tasks"] = dict(enumerate(spec["tasks"]))
spec["communications"] = dict(enumerate(spec["communications"]))
spec["shared_blocks"] = dict(enumerate(spec["shared_blocks"]))
