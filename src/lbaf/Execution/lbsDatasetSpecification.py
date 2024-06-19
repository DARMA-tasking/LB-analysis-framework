from typing import List, Dict, TypedDict, Union

class DatasetSpecification(TypedDict):
    """Dictionary representing specification for a simple dataset"""

    # List of tasks times as a list (index considered as the id) or as a dict { id => time1, id => time2 })
    tasks: Union[List[int],Dict[int,int]]
    # List of shared blocks as a list (index considered as the id) or as a dict { id => size1, id => size2 })
    shared_blocks: Union[List[int],Dict[int,int]]
    # List of communications as a list (index considered as the id) or as a dict { id => size1, id => size2 })
    communications: Union[List[int],Dict[int,int]]
    # Rank distributions / tasks ids per rank id
    ranks: Dict[int,List[int]]
