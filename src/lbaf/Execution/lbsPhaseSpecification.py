from typing import List, Dict, TypedDict, Union, Set, Callable, Optional, cast

class SharedBlockSpecification(TypedDict):
    # The shared block size
    size: float
    # The ID of the unique rank to which a shared block ultimately belong
    home: int
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

class PhaseSpecification(TypedDict):
    """Dictionary representing a phase specification"""

    # Tasks specifications
    tasks: Union[
        List[float], # Tasks volumes as a list (element index=task id)
        Dict[int,float] # Tasks volumes as a dictionary (dictionary key=task id)
    ]

    # Shared blocks specifications
    shared_blocks: Union[
        List[SharedBlockSpecification], # where index = shared block id
        Dict[int,SharedBlockSpecification] # where dictionary key = shared block id
    ]

    # Communications specifications
    communications: Union[
        List[CommunicationSpecification],  # where index = communication id
        Dict[int,CommunicationSpecification] # where dictionary key = communication id
    ]

    # Rank distributions
    ranks: Dict[int,RankSpecification] # where index = rank id

class PhaseSpecificationNormalizer:
    """Provides normalization and denormalization for PhaseSpecification
    where inner sets are represented as lists to improve readability in JSON or YAML
    """

    def __normalize_member(self, data: Union[dict,list], transform: Optional[Callable] = None) -> Union[dict,list]:
        """Normalize a member that can be represented as a dict where key is the item key or as a list
        where id is the index in the list"""

        if isinstance(data, list):
            return [ transform(o) for o in data ] if transform is not None else data
        elif isinstance(data, dict):
            return { o_id:transform(o) for o_id, o in data.items() } if transform is not None else data # pylint: disable=E1101 (no-member)
        else:
            raise RuntimeError("data must be list or dict")

    def normalize(self, spec: PhaseSpecification)-> dict:
        """Normalize a phase specification to represent inner sets as lists

        Note: the sets converted to lists are
        - `self.shared_blocks.tasks`
        - `self.ranks.tasks`
        - `self.ranks.communications`

        This method should be called before json or yaml serialization.
        Denormalization should be executed using the static method json_denormalize
        """

        return {
            "tasks": self.__normalize_member(spec.get("tasks", [])),
            "shared_blocks": self.__normalize_member(
                spec.get("shared_blocks", []),
                lambda b: {
                    "size": b.get("size"),
                    "tasks": list(b.get("tasks", {})),
                    "home": b.get("home"),
                }
            ),
            "communications": self.__normalize_member(spec.get("communications", [])),
            "ranks": self.__normalize_member(
                spec.get("ranks", {}),
                lambda r: {
                    "tasks": list(r.get("tasks", {}))
                }
            )
        }

    def denormalize(self, data: dict)-> PhaseSpecification:
        """Create a phase specification using a definition where sets are represented as lists"""

        return PhaseSpecification({
            "tasks": self.__normalize_member(data.get("tasks", [])),
            "shared_blocks": self.__normalize_member(
                data.get("shared_blocks", []),
                lambda b: SharedBlockSpecification({
                    "size": b.get("size", 0.0),
                    "tasks": set(b.get("tasks", [])),
                    "home": b.get("home")
                })
            ),
            "communications": self.__normalize_member(
                data.get("communications", []),
                lambda c: cast(CommunicationSpecification, c)
            ),
            "ranks": self.__normalize_member(
                data.get("ranks", []),
                lambda r: RankSpecification({
                    "tasks": set(r.get("tasks", []))
                })
            )
        })
