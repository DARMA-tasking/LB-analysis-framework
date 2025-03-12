#
#@HEADER
###############################################################################
#
#                           lbsPhaseSpecification.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
import sys
from typing import List, Dict, TypedDict, Union, Set, Callable, Optional, cast

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

class TaskSpecification(TypedDict):
    # The task time
    time: float
    # The task's sequential ID
    seq_id: int
    # Whether the task is migratable or not
    migratable: bool
    # The task's home rank
    home: int
    # The task's current node
    node: int
    # The collection id
    collection_id: NotRequired[int]
    # User-defined parameters
    user_defined: NotRequired[dict]


class SharedBlockSpecification(TypedDict):
    # The shared block size
    size: float
    # The ID of the unique rank to which a shared block ultimately belong
    home_rank: int
    # The set of tasks accessing this shared block
    tasks: Set[int]
    # the shared block ID
    shared_id: int

CommunicationSpecification = TypedDict('CommunicationSpecification', {
    'size': float,
    'from': int,
    'to': int
})

class RankSpecification(TypedDict):
    # The task ids
    tasks: Set[int]
    id: int
    user_defined: dict

class PhaseSpecification(TypedDict):
    """Dictionary representing a phase specification"""

    # Tasks specifications
    tasks: Union[
        List[TaskSpecification], # where index = task id
        Dict[int,TaskSpecification] # where dictionary key = task id
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

    # Phase id
    id: int

class PhaseSpecificationNormalizer:
    """
    Provides normalization and denormalization for PhaseSpecification
    where inner sets are represented as lists to improve readability in JSON or YAML
    """

    def __normalize_member(self, data: Union[dict,list], transform: Optional[Callable] = None) -> Union[dict,list]:
        """Normalize a member that can be represented as a dict where key is the item key or as a list
        where id is the index in the list
        """

        if isinstance(data, list):
            return [ transform(o) for o in data ] if transform is not None else data
        if isinstance(data, dict):
            return { o_id:transform(o) for o_id, o in data.items() } if transform is not None else data # pylint: disable=E1101 (no-member)
        raise RuntimeError("data must be list or dict")

    def normalize(self, spec: PhaseSpecification)-> dict:
        """Normalize a phase specification to represent inner sets as lists

        Note: the sets converted to lists are
        - `self.shared_blocks.tasks`
        - `self.ranks.tasks`
        - `self.ranks.communications`

        This method should be called before json or yaml serialization.
        Denormalization should be executed using the method denormalize

        Note: the normalized specification data is easier to read and edit in json or yaml.
        """

        return {
            "tasks": self.__normalize_member(spec.get("tasks", {})),
            "shared_blocks": self.__normalize_member(
                spec.get("shared_blocks", []),
                lambda b: {
                    "size": b.get("size"),
                    "tasks": list(b.get("tasks", {})),
                    "home_rank": b.get("home_rank"),
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
        """Create a phase specification from a normalized specification where some lists must
        be converted to sets.

        Detail: the following lists will be converted to sets to ensure each element is unique
        - `data.shared_blocks.tasks`
        - `data.ranks.tasks`
        - `data.ranks.communications`

        This method should be called after json or yaml deserialization.
        This is the reverse implementation of the normalize method.
        """
        def dict_merge(a, b):
            a.update(b)
            return a

        return PhaseSpecification({
            "tasks": self.__normalize_member(
                data.get("tasks", []),
                lambda t: TaskSpecification(dict_merge(
                    { "time": t.get("time", 0.0) },
                    { "seq_id": t.get("seq_id", None)} if "seq_id" in t else {},
                    { "migratable": t.get("migratable", True)} if "migratable" in t else {},
                    { "home": t.get("home", 0)} if "home" in t else {},
                    { "node": t.get("node", 0)} if "node" in t else {},
                    { "collection_id": t.get("collection_id", None)} if "collection_id" in t else {},
                    { "user_defined": t.get("user_defined", {})} if "user_defined" in t else {}
                ))
            ),
            "shared_blocks": self.__normalize_member(
                data.get("shared_blocks", []),
                lambda b: SharedBlockSpecification({
                    "size": b.get("size", 0.0),
                    "tasks": set(b.get("tasks", {})),
                    "home_rank": b.get("home_rank"),
                    "shared_id": b.get("shared_id")
                })
            ),
            "communications": self.__normalize_member(
                data.get("communications", []),
                lambda c: cast(CommunicationSpecification, c)
            ),
            "ranks": self.__normalize_member(
                data.get("ranks", []),
                lambda r: RankSpecification({
                    "tasks": set(r.get("tasks", [])),
                    "id": set(r.get("id", None)),
                    "user_defined": set(r.get("user_defined", {}) if "user_defined" in r else {})
                })
            )
        })
