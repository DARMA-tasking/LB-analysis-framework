from typing import Optional

from .lbsBlock import Block
from .lbsObjectCommunicator import ObjectCommunicator

class Object:
    """A class representing an object with load and communicator

    Constructor arguments:
    :arg seq_id: small int identifier, commonly the task index, defaults to None
    :arg packed_id: alt identifier (generated by vt as a bitpacked value), defaults to None
    :arg r_id: rank ID, defaults to None
    :arg load: the computational time, also known as load, defaults to 0.0
    :arg size: the size, defaults to 0.0
    :arg comm: the communicator, defaults to None
    :arg user_defined: user defined data dict, defaults to None
    :arg subphases: list of subphases, defaults to None
    :arg collection_id: collection id (required for migratable objects)
    """

    def __init__(
        self,
        seq_id: Optional[int] = None,
        packed_id: Optional[int] = None,
        r_id: Optional[int]=None,
        load: float=0.0,
        size: float=0.0,
        comm: Optional[ObjectCommunicator]=None,
        user_defined: dict=None,
        subphases: list=None,
        collection_id: Optional[int] = None):

        # Check that id is provided as defined in LBDatafile schema
        if packed_id is None and seq_id is None:
            raise ValueError('Either packed_id (bit-encoded ID) or i (seq ID) must be provided.')

        # Object ID
        if seq_id is not None and (
            not isinstance(seq_id, int) or isinstance(seq_id, bool)):
            raise TypeError(
                f"seq_id: incorrect type {type(seq_id)}")
        self.__seq_id: Optional[int] = seq_id

        if packed_id is not None and (
            not isinstance(packed_id, int) or isinstance(packed_id, bool)):
            raise TypeError(
                f"packed_id: incorrect type {type(packed_id)}")
        self.__packed_id: Optional[int] = packed_id

        # Nonnegative load required to perform the work of this object
        if not isinstance(load, (int, float)) or isinstance(load, bool) or load < 0.0:
            raise TypeError(
                f"load: incorrect type {type(load)} or value: {load}")
        self.__load = float(load)

        # Nonnegative size required to for memory footprint of this object
        if not isinstance(size, (int, float)) or isinstance(size, bool) or size < 0.0:
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        self.__size = float(size)

        # Rank to which object is currently assigned if defined
        if not(r_id is None or isinstance(r_id, int)) or isinstance(r_id, bool):
            raise TypeError(
                f"r_id: incorrect type {type(r_id)}")
        self.__rank_id = r_id

        # Communication graph of this object if defined
        if not(isinstance(comm, ObjectCommunicator) or comm is None):
            raise TypeError(
                f"comm: {comm} is of type {type(comm)}. Must be <class 'ObjectCommunicator'>.")
        self.__communicator: ObjectCommunicator = comm

        # Initialize other instance variables
        self.__overhead = 0.0
        self.__shared_block: Optional[Block] = None

        # Initialize currently unused parameters (for writing back out)
        self.__unused_params = {}

        # collection_id is not used in LBAF but is required for migratable objects in vt
        self.__collection_id = collection_id

        # Retrieve and set optionally defined fields
        if isinstance(user_defined, dict) or user_defined is None:
            self.__user_defined = user_defined
        else:
            raise TypeError(f"user_defined: {user_defined} is of type {type(user_defined)}. Must be <class 'dict'>.")
        if user_defined:
            # Object size is by definition its memory footprint
            if not isinstance((
                size := user_defined.get("task_footprint_bytes", 0.0)), (int, float)) or isinstance(size, bool) or size < 0.0:
                raise TypeError(
                    f"size: incorrect type {type(size)} or value: {size}")
            else:
                self.__size = float(size)

            # Object overhead is by definition its additional working memory
            if not isinstance((
                overhead := user_defined.get("task_working_bytes", 0.0)), (int, float)) or isinstance(overhead, bool) or overhead < 0.0:
                raise TypeError(
                    f"overhead: incorrect type {type(overhead)} or value: {overhead}")
            else:
                self.__overhead = float(overhead)

        # Sub-phases
        if isinstance(subphases, list) or subphases is None:
            self.__subphases = subphases
        else:
            raise TypeError(f"subphases: {subphases} is of type {type(subphases)} but must be <class 'list'>")

    def __repr__(self):
        return f"Object id: {self.__seq_id}, load: {self.__load}"

    def get_id(self) -> int:
        """Return object bit-packed ID if available. Else return the object seq ID"""
        return self.__packed_id if self.__packed_id is not None else self.__seq_id

    def get_packed_id(self) -> Optional[int]:
        """Return object bit-packed ID (seq_id, home_id, migratable)."""
        return self.__packed_id

    def get_seq_id(self) -> Optional[int]:
        """Return object seq ID."""
        return self.__seq_id

    def get_collection_id(self) -> Optional[int]:
        """Return object collection ID (required for migratable objects)."""
        return self.__collection_id

    def set_collection_id(self, collection_id: Optional[int]):
        """ Set object collection ID (required for migratable objects)."""
        self.__collection_id = collection_id

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

    def get_user_defined(self) -> dict:
        """Return optionally defined fields"""
        return self.__user_defined

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

    def get_max_volume(self) -> float:
        """Return the maximum bytes received or sent by object."""
        return self.__communicator.get_max_volume() if self.__communicator else 0

    def set_rank_id(self, r_id: int) -> None:
        """Assign object to rank ID"""
        self.__rank_id = r_id

    def get_rank_id(self) -> int:
        """Return ID of rank to which object is currently assigned."""
        return self.__rank_id

    def set_shared_block(self, b: Optional[Block]) -> None:
        """Assign shared memory block when necessary."""
        if b is not None and not isinstance(b, Block):
            raise TypeError(f"shared block: incorrect type {type(b)}")
        self.__shared_block = b

    def get_shared_block(self) -> Optional[Block]:
        """Return shared memory block assigned to object."""
        return self.__shared_block

    def get_shared_id(self) -> Optional[int]:
        """Return ID of shared memory block assigned to object."""
        return self.__shared_block.get_id() if self.__shared_block is not None else None

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

    def set_unused_params(self, unused_params: dict):
        """Assign any extraneous parameters."""
        self.__unused_params = unused_params

    def get_unused_params(self) -> dict:
        """Return all current unused parameters."""
        return self.__unused_params
