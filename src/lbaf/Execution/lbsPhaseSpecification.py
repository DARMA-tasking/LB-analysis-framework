from typing import List, Dict, TypedDict, Union, Set

class SharedBlockSpecification(TypedDict):
    # The shared block size
    size: float
    # The set of tasks accessing this shared block
    tasks: Set[int]

CommunicationSpecification = TypedDict('CommunicationSpecification', {
    'size': float,
    'from': int,
    'to': int
})

class RankSpecification(TypedDict):
    # The task ids
    tasks: Set[int]
    # The communication ids
    communications: Set[int]

class PhaseSpecification(TypedDict):
    """Dictionary representing a phase specification"""

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
    ranks: Dict[int,RankSpecification]
