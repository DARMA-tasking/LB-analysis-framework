from typing import List, Dict, TypedDict, Union, Set

class SharedBlockSpecification(TypedDict):
    # The shared block size
    size: float
    # The set of tasks accessing this shared block
    tasks: Set[int]

class CommunicationSpecification(TypedDict):
    # The shared block size
    size: float
    # The set of tasks accessing this shared block
    from_: int
    to: int

class PhaseSpecification(TypedDict):
    """Dictionary representing specification for a simple dataset"""
    # List of tasks times as a list (index considered as the id) or as a dict { id => time1, id => time2 })
    tasks: Union[List[float],Dict[int,float]]

    # List of shared blocks sizes as
    # - a dict { shared_block_1_id => shared_block_1, shared_block_2_id => shared_block_2 })
    # - a list (shared block id is the index in the list)
    shared_blocks: Union[List[SharedBlockSpecification],Dict[int,SharedBlockSpecification]]

    # List of communications volumes as
    # - a dict { com1_id => com1, com2_id => com2 })
    # - a list (communication id is the index in the list)
    communications: Union[List[CommunicationSpecification],Dict[int,CommunicationSpecification]]

    # Rank distributions / tasks ids per rank id
    ranks: Dict[int,Set[int]]

    @staticmethod
    def create_sample():
        """Creates a new sample specification as represented by diagram specified in issue #506"""
        specs = PhaseSpecification({
            'tasks': [2.0, 3.5, 5.0],
            'communications': [
                {
                    "size": 10000.0, # c1 (size)
                    "from_": 0, # from t1
                    "to": 2 # to t3
                },
                {
                    "size": 15000.0, # c2 (size)
                    "from_": 1, # from t2
                    "to": 2 # to t3
                },
                {
                    "size": 20000.0, # c3 (size)
                    "from_": 2, # from t3
                    "to": 1 # to t2
                },
                {
                    "size": 25000.0, # c4 (size)
                    "from_": 0, # from t1
                    "to": 1 # to t2
                }
            ],
            "shared_blocks": [
                # S1
                {
                    'size': 10000.0,
                    'tasks': { 0, 1 }
                },
                #S2
                {
                    'size': 15000.0,
                    'tasks': { 2 }
                }
            ],
            "ranks": {
                0: { 0, 1 },
                1: { 2 }
            }
        })

        return specs
