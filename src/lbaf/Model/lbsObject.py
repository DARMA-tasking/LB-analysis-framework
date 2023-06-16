from typing import Optional

from .lbsBlock import Block
from .lbsObjectCommunicator import ObjectCommunicator


class Object:
    """A class representing an object with load and communicator"""

    def __init__(
        self,
        i: int,
        r_id: Optional[int]=None,
        load: float=0.0,
        size: float=0.0,
        comm: Optional[ObjectCommunicator]=None,
        user_defined: dict=None,
        subphases: list=None):

        # Object index
        if not isinstance(i, int) or isinstance(i, bool):
            raise TypeError(
                f"i: incorrect type {type(i)}")
        self.__index = i

        # Nonnegative load required to perform the work of this object
        if not isinstance(load, float) or load < 0.0:
            raise TypeError(
                f"load: incorrect type {type(load)} or value: {load}")
        self.__load = load

        # Nonnegative size required to for memory footprint of this object
        if not isinstance(size, float) or size < 0.0:
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        self.__size = size

        # Rank to which object is currently assigned if defined
        if not(r_id is None or isinstance(r_id, int)) or isinstance(r_id, bool):
            raise TypeError(
                f"r_id: incorrect type {type(r_id)}")
        self.__rank_id = r_id

        # Communication graph of this object if defined
        if not(isinstance(comm, ObjectCommunicator) or comm is None):
            raise TypeError(
                f"comm: {comm} is of type {type(comm)}. Must be <class 'ObjectCommunicator'>.")
        self.__communicator = comm

        # Initialize other instance variables
        self.__overhead = 0.0
        self.__shared_block = None

        # Retrieve and set optionally defined fields
        if isinstance(user_defined, dict) or user_defined is None:
            self.__user_defined = user_defined
        else:
            raise TypeError(f"user_defined: {user_defined} is of type {type(user_defined)}. Must be <class 'dict'>.")
        if user_defined:
            # Object size is by definition its memory footprint
            if not isinstance((
                size := user_defined.get("task_footprint_bytes")), float) or size < 0.0:
                raise TypeError(
                    f"size: incorrect type {type(size)} or value: {size}")
            else:
                self.__size = size

            # Object overhead is by definition its additional working memory
            if not isinstance((
                overhead := user_defined.get("task_working_bytes")), float) or overhead < 0.0:
                raise TypeError(
                    f"overhead: incorrect type {type(overhead)} or value: {overhead}")
            else:
                self.__overhead = overhead

        # Sub-phases
        if isinstance(subphases, list) or subphases is None:
            self.__subphases = subphases
        else:
            raise TypeError(f"subphases: {subphases} is of type {type(subphases)} but must be <class 'list'>")

    def __repr__(self):
        return f"Object id: {self.__index}, load: {self.__load}"

    def get_id(self) -> int:
        """Return object ID."""
        return self.__index

    def set_load(self, load: float):
        """ Set object load."""
        self.__load = load

    def get_load(self) -> float:
        """Return object load."""
        return self.__load

    def get_size(self) -> float:
        """Return object size."""
        return self.__size

    def get_overhead(self) -> float:
        """Return additional runtime memory of object."""
        return self.__overhead

    def get_sent(self) -> dict:
        """Return communications sent by object to other objects."""
        return self.__communicator.get_sent() if self.__communicator else {}

    def get_received(self) -> dict:
        """Return communications received by object from other objects."""

        return self.__communicator.get_received() if self.__communicator else {}

    def get_received_volume(self) -> float:
        """Return volume of communications received by object."""
        return sum([v for v in self.__communicator.get_received().values()]) if self.__communicator else 0

    def get_sent_volume(self) -> float:
        """Return volume of communications sent by object."""
        return sum([v for v in self.__communicator.get_sent().values()]) if self.__communicator else 0

    def set_rank_id(self, r_id: int) -> None:
        """Assign object to rank ID"""
        self.__rank_id = r_id

    def get_rank_id(self) -> int:
        """Return ID of rank to which object is currently assigned."""
        return self.__rank_id

    def set_shared_block(self, b: Block) -> None:
        """Assign shared memory block when necessary."""
        if not isinstance(b, Block):
            raise TypeError(f"shared block: incorrect type {type(b)}")
        self.__shared_block = b

    def get_shared_block(self) -> int:
        """Return shared memory block assigned to object."""
        return self.__shared_block

    def get_shared_block_id(self) -> int:
        """Return ID of shared memory block assigned to object."""
        return self.__shared_block.get_id()

    def has_communicator(self) -> bool:
        """Return whether the object has communication graph data."""
        return self.__communicator is not None

    def get_communicator(self) -> ObjectCommunicator:
        """Return the communication graph for this object."""
        return self.__communicator

    def set_communicator(self, c) -> None:
        """Assign the communication graph for this object."""

        if not isinstance(c, ObjectCommunicator):
            raise TypeError(f"object communicator: incorrect type {type(c)}")
        self.__communicator = c

    def get_subphases(self) -> list:
        """Return subphases of this object."""
        return self.__subphases
