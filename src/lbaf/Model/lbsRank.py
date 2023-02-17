import sys
import math
import random as rnd
from logging import Logger

from .lbsMessage import Message
from .lbsObject import Object
from ..Utils.exception_handler import exc_handler


class Rank:
    """ A class representing a rank to which objects are assigned
    """

    def __init__(
        self,
        i: int,
        logger: Logger,
        mo: set = None,
        so: set = None):

        # Assign logger to instance variable
        self.__logger = logger

        # Member variables passed by constructor
        self.__index = i
        self.__migratable_objects = set()
        if mo is not None:
            for o in mo:
                self.__migratable_objects.add(o)
        self.__sentinel_objects = set()
        if so is not None:
            for o in so:
                self.__sentinel_objects.add(o)

        # Initialize other instance variables
        self.__size = 0.0

        # Start with empty shared blokck information
        self.__shared_blocks = {}

        # No information about peers is known initially
        self.__known_loads = {}

        # No message was received initially
        self.round_last_received = 0

    def __repr__(self):
        return f"<Rank index: {self.__index}>"

    def get_id(self) -> int:
        """ Return rank ID."""
        return self.__index

    def get_size(self) -> float:
        """ Return object size."""
        return self.__size

    def set_size(self, size: float):
        """ Set rank working memory, called size."""
        # Nonnegative size required to for memory footprint of this rank
        if not isinstance(size, float) or size < 0.0:
            sys.excepthook = exc_handler
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        self.__size = size

    def set_shared_blocks(self, sb: dict):
        """ Set rank shared memory blocks."""
        # A dictionary is required to for shared memory blocks
        if not isinstance(sb, dict):
            sys.excepthook = exc_handler
            raise TypeError(
                f"shared blocks: incorrect type {type(sb)}")

        # Assign shared blocks
        self.__shared_blocks = sb

    def add_shared_block(self, b_id: int, b_sz: float, o_id: int):
        """ Add rank shared memory block."""
        # A (float, int) pair is required to add shared memory block
        if not isinstance(b_id, int):
            sys.excepthook = exc_handler
            raise TypeError(
                f"shared block ID: incorrect type {type(b_id)}")
        if not isinstance(b_sz, float):
            sys.excepthook = exc_handler
            raise TypeError(
                f"shared block memory: incorrect type {type(b_sz)}")
        if not isinstance(o_id, int):
            sys.excepthook = exc_handler
            raise TypeError(
                f"shared block object ID: incorrect type {type(o_id)}")

        # Update instance variables; no checks are performed
        self.__shared_blocks[b_id] = (b_sz, set([o_id]))

    def delete_shared_block(self, b_id: int):
        """ Delete shared memory block."""
        if b_id not in self.__shared_blocks:
            sys.excepthook = exc_handler
            raise TypeError(
                f"shared block ID: {b_id} not present on rank {self.get_id()}")

        # Delete shared block
        del self.__shared_blocks[b_id]

    def get_shared_blocks(self) -> dict:
        """ Return shared memory blocks."""

        return self.__shared_blocks

    def get_shared_block_memory(self, block_id: int) -> float:
        """ Return shared memory block size."""

        return self.__shared_blocks[block_id][0]

    def get_shared_memory(self):
        """ Return total shared memory on rank."""

        return float(sum([x[0] for x in self.__shared_blocks.values()]))

    def get_objects(self) -> set:
        """ Return all objects assigned to rank."""

        return self.__migratable_objects.union(self.__sentinel_objects)

    def add_migratable_object(self, o: Object) -> None:
        """ Add object to migratable objects."""

        return self.__migratable_objects.add(o)

    def get_migratable_objects(self) -> set:
        """ Return migratable objects assigned to rank."""

        return self.__migratable_objects

    def add_sentinel_object(self, o: Object) -> None:
        """ Add object to sentinel objects."""

        return self.__sentinel_objects.add(o)

    def get_sentinel_objects(self) -> set:
        """ Return sentinel objects assigned to rank."""

        return self.__sentinel_objects

    def get_number_of_sentinel_objects(self) -> int:
        """ Return number of sentinel objects assigned to rank."""

        return len(self.__sentinel_objects)

    def get_object_ids(self) -> list:
        """ Return IDs of all objects assigned to rank."""

        return [o.get_id() for o in self.__migratable_objects.union(self.__sentinel_objects)]

    def get_migratable_object_ids(self) -> list:
        """ Return IDs of migratable objects assigned to rank."""

        return [o.get_id() for o in self.__migratable_objects]

    def get_sentinel_object_ids(self) -> list:
        """ Return IDs of sentinel objects assigned to rank."""

        return [o.get_id() for o in self.__sentinel_objects]

    def is_sentinel(self, o: Object) -> list:
        """ Return whether given object is sentinel of rank."""

        if o in self.__sentinel_objects:
            return True
        else:
            return False

    def get_known_loads(self) -> dict:
        """ Return loads of peers know to self."""

        return self.__known_loads

    def get_targets(self) -> list:
        """ Return list of potential targets for object transfers."""

        # No potential targets for loadless ranks
        if not self.get_load() > 0.:
            return []

        # Remove self from list of targets
        targets = self.get_known_loads()
        del targets[self]
        return targets

    def remove_migratable_object(self, o: Object, p_dst: "Rank"):
        """ Remove migratable able object from self object sent to peer."""

        # Remove object from those assigned to self
        self.__migratable_objects.remove(o)

        # Update known load when destination is already known
        if self.__known_loads and p_dst in self.__known_loads:
            self.__known_loads[p_dst] += o.get_load()

    def get_load(self) -> float:
        """ Return total load on rank."""

        return sum([o.get_load() for o in self.__migratable_objects.union(self.__sentinel_objects)])

    def get_migratable_load(self) -> float:
        """ Return migratable load on rank."""

        return sum([o.get_load() for o in self.__migratable_objects])

    def get_sentinel_load(self) -> float:
        """ Return sentinel load oon rank."""

        return sum([o.get_load() for o in self.__sentinel_objects])

    def get_received_volume(self):
        """ Return volume received by objects assigned to rank from other ranks."""

        # Iterate over all objects assigned to rank
        volume = 0
        obj_set = self.__migratable_objects.union(self.__sentinel_objects)
        for o in obj_set:
            # Skip objects without communication
            if not o.has_communicator():
                continue

            # Add total volume received from non-local objects
            volume += sum([v for k, v in o.get_communicator().get_received().items() if k not in obj_set])

        # Return computed volume
        return volume

    def get_sent_volume(self):
        """ Return volume sent by objects assigned to rank to other ranks."""

        # Iterate over all objects assigned to rank
        volume = 0
        obj_set = self.__migratable_objects.union(self.__sentinel_objects)
        for o in obj_set:
            # Skip objects without communication
            if not o.has_communicator():
                continue

            # Add total volume sent to non-local objects
            volume += sum([
                v for k, v in o.get_communicator().get_sent().items()
                if k not in obj_set])

        # Return computed volume
        return volume

    def get_max_object_level_memory(self) -> float:
        """ Return maximum object-level memory on rank."""

        # Iterate over all objects assigned to rank
        total_size, max_overhead = 0.0, 0.0
        for o in self.__migratable_objects.union(self.__sentinel_objects):
            # Update maximum runtime overhead as needed
            if (x := o.get_overhead()) > max_overhead:
                max_overhead = x

            # Tally current obect size in total size
            total_size += o.get_size()

        # Return maximum object-level memory for this rank
        return total_size + max_overhead

    def get_max_memory_usage(self) -> float:
        """ Return maximum memory usage on rank."""

        return self.__size + self.get_shared_memory() + self.get_max_object_level_memory()

    def reset_all_load_information(self):
        """ Reset all load information known to self."""

        # Reset information about known peers
        self.__known_loads = {}

    def initialize_message(self, loads: set, f: int):
        """ Initialize message to be sent to selected peers."""

        # Retrieve current load on this rank
        l = self.get_load()

        # Make rank aware of own load
        self.__known_loads[self] = l

        # Create load message tagged at first round
        msg = Message(1, self.__known_loads)

        # Broadcast message to pseudo-random sample of ranks excluding self
        return rnd.sample(set(loads).difference([self]), min(f, len(loads) - 1)), msg

    def forward_message(self, r, s, f):
        """ Forward information message to sample of selected peers."""

        # Create load message tagged at current round
        msg = Message(r, self.__known_loads)

        # Compute complement of set of known peers
        complement = set(self.__known_loads).difference([self])

        # Forward message to pseudo-random sample of ranks
        return rnd.sample(complement, min(f, len(complement))), msg

    def process_message(self, msg):
        """ Update internals when message is received."""

        # Assert that message has the expected type
        if not isinstance(msg, Message):
            self.__logger.warning(f"Attempted to pass message of incorrect type {type(msg)}. Ignoring it.")

        # Update load information
        self.__known_loads.update(msg.get_content())

        # Update last received message index
        self.round_last_received = msg.get_round()

    def compute_transfer_cmf(self, transfer_criterion, objects: list, targets: dict, strict=False):
        """ Compute CMF for the sampling of transfer targets."""

        # Initialize criterion values
        c_values = {}
        c_min, c_max = math.inf, -math.inf

        # Iterate over potential targets
        for p_dst in targets.keys():
            # Compute value of criterion for current target
            c = transfer_criterion.compute(objects, self, p_dst)

            # Do not include rejected targets for strict CMF
            if strict and c < 0.:
                continue

            # Update criterion values
            c_values[p_dst] = c
            if c < c_min:
                c_min = c
            if c > c_max:
                c_max = c

        # Initialize CMF depending on singleton or non-singleton support
        if c_min == c_max:
            # Sample uniformly if all criteria have same value
            cmf = {k: 1. / len(c_values) for k in c_values.keys()}
        else:
            # Otherwise, use relative weights
            c_range = c_max - c_min
            cmf = {k: (v - c_min) / c_range for k, v in c_values.items()}

        # Compute CMF
        sum_p = 0.
        for k, v in cmf.items():
            sum_p += v
            cmf[k] = sum_p

        # Return normalized CMF and criterion values
        return {k: v / sum_p for k, v in cmf.items()}, c_values
