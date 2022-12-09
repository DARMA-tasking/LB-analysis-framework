import sys
import copy
import math
import random as rnd
from logging import Logger

from .lbsBlock import Block
from .lbsMessage import Message
from .lbsObject import Object
from ..Utils.exception_handler import exc_handler


class Rank:
    """A class representing a rank to which objects are assigned."""

    def __init__(
        self,
        logger: Logger,
        r_id: int = -1,
        mo: set = None,
        so: set = None):

        # Assign logger to instance variable
        self.__logger = logger

        # Member variables passed by constructor
        self.__index = r_id
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

    def copy(self, rank):
        """Specialized copy method."""
        # Copy all flat member variables
        self.__index = rank.get_id()
        self.__size = rank.get_size()
        self.round_last_received = rank.round_last_received

        # Shallow copy owned objects
        self.__shared_blocks = copy.copy(rank.__shared_blocks)
        self.__known_loads = copy.copy(rank.__known_loads)
        self.__sentinel_objects = copy.copy(rank.__sentinel_objects)
        self.__migratable_objects = copy.copy(rank.__migratable_objects)

    def __lt__(self, other):
        return self.get_load() < other.get_load()

    def __repr__(self):
        return f"<Rank index: {self.__index}>"

    def get_id(self) -> int:
        """Return rank ID."""
        return self.__index

    def get_size(self) -> float:
        """Return object size."""
        return self.__size

    def set_size(self, size: float):
        """Set rank working memory, called size."""
        # Nonnegative size required for memory footprint of this rank
        if not isinstance(size, float) or size < 0.0:
            sys.excepthook = exc_handler
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        self.__size = size

    def get_shared_block_ids(self) -> set:
        """Return IDs of shared blocks."""
        return {b.get_id() for b in self.__shared_blocks}

    def set_shared_blocks(self, blocks: set):
        """Set rank shared memory blocks."""
        # A set is required for shared memory blocks
        if not isinstance(blocks, set):
            sys.excepthook = exc_handler
            raise TypeError(
                f"shared blocks: incorrect type {type(blocks)}")

        # Assign shared blocks
        self.__shared_blocks = blocks

    def add_shared_block(self, block: Block):
        """Add rank shared memory block."""
        # A Block instance is required to add shared memory block
        if not isinstance(block, Block):
            sys.excepthook = exc_handler
            raise TypeError(
                f"block: incorrect type {type(block)}")

        # Update instance variable without ownership check
        self.__shared_blocks.add(block)

    def delete_shared_block(self, block: Block):
        """Try to delete shared memory block."""
        try:
            self.__shared_blocks.remove(block)
        except Exception as err:
            sys.excepthook = exc_handler
            raise TypeError(
                f"no shared block with ID {block.get_id()} to deleted from on rank {self.get_id()}") from err

    def get_shared_block_with_id(self, b_id: int) -> Block:
        """Return shared memory block with given ID when it exists."""
        for block in self.__shared_blocks:
            if block.get_id() == b_id:
                return block
        return None

    def get_number_of_shared_blocks(self) -> float:
        """Return number of shared memory blocks on rank."""
        return len(self.__shared_blocks)

    def get_number_of_homed_blocks(self) -> float:
        """Return number of memory blocks on rank also homed there."""
        return sum(
            b.get_home_id() == self.get_id()
            for b in self.__shared_blocks)

    def get_number_of_uprooted_blocks(self) -> float:
        """Return number of uprooted memory blocks on rank."""
        return len(self.__shared_blocks) - self.get_number_of_homed_blocks()

    def get_homed_blocks_ratio(self) -> float:
        """Return fraction of memory blocks on rank also homed there."""
        if len(self.__shared_blocks):
            return self.get_number_of_homed_blocks() / len(self.__shared_blocks)
        else:
            return math.nan

    def get_shared_memory(self):
        """Return total shared memory on rank."""
        return float(sum([b.get_size() for b in self.__shared_blocks]))

    def get_objects(self) -> set:
        """Return all objects assigned to rank."""
        return self.__migratable_objects.union(self.__sentinel_objects)

    def get_number_of_objects(self) -> int:
        """Return number of objects assigned to rank."""
        return len(self.__sentinel_objects) + len(self.__migratable_objects)

    def add_migratable_object(self, o: Object) -> None:
        """Add object to migratable objects."""
        return self.__migratable_objects.add(o)

    def get_migratable_objects(self) -> set:
        """Return migratable objects assigned to rank."""
        return self.__migratable_objects

    def add_sentinel_object(self, o: Object) -> None:
        """Add object to sentinel objects."""
        return self.__sentinel_objects.add(o)

    def get_sentinel_objects(self) -> set:
        """Return sentinel objects assigned to rank."""
        return self.__sentinel_objects

    def get_object_ids(self) -> list:
        """Return IDs of all objects assigned to rank."""
        return [o.get_id() for o in self.__migratable_objects.union(self.__sentinel_objects)]

    def get_migratable_object_ids(self) -> list:
        """Return IDs of migratable objects assigned to rank."""
        return [o.get_id() for o in self.__migratable_objects]

    def get_sentinel_object_ids(self) -> list:
        """Return IDs of sentinel objects assigned to rank."""
        return [o.get_id() for o in self.__sentinel_objects]

    def is_sentinel(self, o: Object) -> list:
        """Return whether given object is sentinel of rank."""
        if o in self.__sentinel_objects:
            return True
        else:
            return False

    def get_known_loads(self) -> dict:
        """Return loads of peers know to self."""
        return self.__known_loads

    def add_known_load(self, rank):
        """Make rank known to self if not already known."""
        self.__known_loads.setdefault(rank, rank.get_load())

    def get_targets(self) -> list:
        """Return list of potential targets for object transfers."""
        # No potential targets for loadless ranks
        if not self.get_load() > 0.:
            return []

        # Remove self from list of targets
        targets = self.get_known_loads()
        del targets[self]
        return targets

    def remove_migratable_object(self, o: Object, r_dst: "Rank"):
        """Remove migratable able object from self object sent to peer."""
        # Remove object from those assigned to self
        self.__migratable_objects.remove(o)

        # Update known load when destination is already known
        if self.__known_loads and r_dst in self.__known_loads:
            self.__known_loads[r_dst] += o.get_load()

    def get_load(self) -> float:
        """Return total load on rank."""
        return sum([o.get_load() for o in self.__migratable_objects.union(self.__sentinel_objects)])

    def get_migratable_load(self) -> float:
        """Return migratable load on rank."""
        return sum([o.get_load() for o in self.__migratable_objects])

    def get_sentinel_load(self) -> float:
        """Return sentinel load oon rank."""
        return sum([o.get_load() for o in self.__sentinel_objects])

    def get_received_volume(self):
        """Return volume received by objects assigned to rank from other ranks."""
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
        """Return volume sent by objects assigned to rank to other ranks."""
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
        """Return maximum object-level memory on rank."""
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
        """Return maximum memory usage on rank."""
        return self.__size + self.get_shared_memory() + self.get_max_object_level_memory()

    def reset_all_load_information(self):
        """Reset all load information known to self."""
        # Reset information about known peers
        self.__known_loads = {}

    def initialize_message(self, loads: set, f: int):
        """Initialize message to be sent to selected peers."""
        # Retrieve current load on this rank
        l = self.get_load()

        # Make rank aware of own load
        self.__known_loads[self] = l

        # Create load message tagged at first round
        msg = Message(1, self.__known_loads)

        # Broadcast message to pseudo-random sample of ranks excluding self
        return rnd.sample(list(loads.difference([self])), min(f, len(loads) - 1)), msg

    def forward_message(self, information_round, _rank_set, fanout):
        """Forward information message to sample of selected peers."""
        # Create load message tagged at current round
        msg = Message(information_round, self.__known_loads)

        # Compute complement of set of known peers
        complement = set(self.__known_loads).difference([self])

        # Forward message to pseudo-random sample of ranks
        return rnd.sample(list(complement), min(fanout, len(complement))), msg

    def process_message(self, msg):
        """Update internals when message is received."""
        # Assert that message has the expected type
        if not isinstance(msg, Message):
            self.__logger.warning(f"Attempted to pass message of incorrect type {type(msg)}. Ignoring it.")

        # Update load information
        self.__known_loads.update(msg.get_content())

        # Update last received message index
        self.round_last_received = msg.get_round()

    def compute_transfer_cmf(self, transfer_criterion, objects: list, targets: dict, strict=False):
        """Compute CMF for the sampling of transfer targets."""
        # Initialize criterion values
        c_values = {}
        c_min, c_max = math.inf, -math.inf

        # Iterate over potential targets
        for r_dst in targets.keys():
            # Compute value of criterion for current target
            c_dst = transfer_criterion.compute(self, objects, r_dst)

            # Do not include rejected targets for strict CMF
            if strict and c_dst < 0.:
                continue

            # Update criterion values
            c_values[r_dst] = c_dst
            if c_dst < c_min:
                c_min = c_dst
            if c_dst > c_max:
                c_max = c_dst

        # Initialize CMF depending on singleton or non-singleton support
        if c_min == c_max:
            # Sample uniformly if all criteria have same value
            cmf = {k: 1.0 / len(c_values) for k in c_values.keys()}
        else:
            # Otherwise, use relative weights
            c_range = c_max - c_min
            cmf = {k: (v - c_min) / c_range for k, v in c_values.items()}

        # Compute CMF
        sum_p = 0.0
        for k, v in cmf.items():
            sum_p += v
            cmf[k] = sum_p

        # Return normalized CMF and criterion values
        return {k: v / sum_p for k, v in cmf.items()}, c_values
