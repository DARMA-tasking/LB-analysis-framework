#
#@HEADER
###############################################################################
#
#                                  lbsRank.py
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
import copy
import math
from logging import Logger
from typing import Optional

from .lbsBlock import Block
from .lbsObject import Object
from .lbsQOIDecorator import qoi

class Rank:
    """A class representing a rank to which objects are assigned."""

    def __init__(
        self,
        logger: Logger,
        r_id: int = -1,
        migratable_objects: set = None,
        sentinel_objects: set = None):

        # Assign logger to instance variable
        self.__logger = logger #pylint:disable=unused-private-member

        # Member variables passed by constructor
        self.__index = r_id
        self.__migratable_objects = set()
        if migratable_objects is not None:
            for o in migratable_objects:
                self.__migratable_objects.add(o)
        self.__sentinel_objects = set()
        if sentinel_objects is not None:
            for o in sentinel_objects:
                self.__sentinel_objects.add(o)

        # Initialize other instance variables
        self.__size = 0.0

        # Start with empty shared block information
        self.__shared_blocks = set()

        # Start with empty metadata
        self.__metadata = {}

    def copy(self, rank):
        """Specialized copy method."""
        # Copy all flat member variables
        self.__index = rank.get_id()
        self.__size = rank.get_size()

        # Shallow copy owned objects
        self.__shared_blocks = copy.copy(rank.__shared_blocks)
        self.__sentinel_objects = copy.copy(rank.__sentinel_objects)
        self.__migratable_objects = copy.copy(rank.__migratable_objects)

    def __lt__(self, other):
        return self.get_load() < other.get_load()

    def __repr__(self):
        return f"<Rank index: {self.__index}>"

    @qoi
    def get_id(self) -> int:
        """Return rank ID."""
        return self.__index

    @qoi
    def get_size(self) -> float:
        """Return rank working memory."""
        return self.__size

    def set_size(self, size):
        """Set rank working memory, called size."""
        # Nonnegative size required for memory footprint of this rank
        if not isinstance(size, (int, float)) or isinstance(size, bool) or size < 0.0:
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        self.__size = float(size)

    def get_metadata(self) -> dict:
        """Return original metadata."""
        return self.__metadata

    def set_metadata(self, metadata: dict):
        """Set rank's metadata."""
        self.__metadata = metadata

    def get_shared_ids(self) -> set:
        """Return IDs of shared blocks."""
        return {b.get_id() for b in self.__shared_blocks}

    def set_shared_blocks(self, blocks: set):
        """Set rank shared memory blocks."""
        # A set is required for shared memory blocks
        if not isinstance(blocks, set):
            self.__logger.error(f"shared blocks: incorrect type {type(blocks)}")
            raise SystemExit(1)

        # Assign shared blocks
        self.__shared_blocks = blocks

    def add_shared_block(self, block: Block):
        """Add rank shared memory block."""
        # A Block instance is required to add shared memory block
        if not isinstance(block, Block):
            self.__logger.error(f"block: incorrect type {type(block)}")
            raise SystemExit(1)

        # Update instance variable without ownership check
        self.__shared_blocks.add(block)

    def delete_shared_block(self, block: Block):
        """Try to delete shared memory block."""
        try:
            self.__shared_blocks.remove(block)
        except Exception as err:
            self.__logger.error(
                f"no shared block with ID {block.get_id()} to delete on rank {self.get_id()}")
            raise SystemExit(1) from err

    def get_shared_block_with_id(self, b_id: int) -> Block:
        """Return shared memory block with given ID when it exists."""
        for block in self.__shared_blocks:
            if block.get_id() == b_id:
                return block
        return None

    @qoi
    def get_number_of_shared_blocks(self) -> float:
        """Return number of shared memory blocks on rank."""
        return len(self.__shared_blocks)

    @qoi
    def get_number_of_homed_blocks(self) -> float:
        """Return number of memory blocks on rank also homed there."""
        return sum(
            b.get_home_id() == self.get_id()
            for b in self.__shared_blocks)

    @qoi
    def get_number_of_uprooted_blocks(self) -> float:
        """Return number of uprooted memory blocks on rank."""
        return len(self.__shared_blocks) - self.get_number_of_homed_blocks()

    @qoi
    def get_homed_blocks_ratio(self) -> float:
        """Return fraction of memory blocks on rank also homed there."""
        if len(self.__shared_blocks) > 0:
            return self.get_number_of_homed_blocks() / len(self.__shared_blocks)
        return math.nan

    @qoi
    def get_shared_memory(self):
        """Return total shared memory on rank."""
        return float(sum(b.get_size() for b in self.__shared_blocks))

    def get_objects(self) -> set:
        """Return all objects assigned to rank."""
        return self.__migratable_objects.union(self.__sentinel_objects)

    @qoi
    def get_number_of_objects(self) -> int:
        """Return number of objects assigned to rank."""
        return len(self.__sentinel_objects) + len(self.__migratable_objects)

    def add_migratable_object(self, o: Object, fallback_collection_id: Optional[int] = 7) -> None:
        """Add object to migratable objects."""
        # Perform sanity checks
        if o.get_collection_id() is None:
            if fallback_collection_id is not None:
                o.set_collection_id(fallback_collection_id)
            if o.get_collection_id() is None:
                self.__logger.error(
                    f"`collection_id` parameter is required for object with id={o.get_id()}"
                    " because it is migratable")
                raise SystemExit(1)

        # Add migratable object and return resulting set
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

    def is_migratable(self, o: Object) -> bool:
        """Return whether given object is migratable."""
        return o in self.__migratable_objects

    def is_sentinel(self, o: Object) -> bool:
        """Return whether given object is sentinel of rank."""
        return o in self.__sentinel_objects

    def remove_migratable_object(self, o: Object):
        """Remove objects from migratable objects."""
        self.__migratable_objects.remove(o)

    @qoi
    def get_load(self) -> float:
        """Return total load on rank."""
        return sum(o.get_load() for o in self.__migratable_objects.union(self.__sentinel_objects))

    @qoi
    def get_migratable_load(self) -> float:
        """Return migratable load on rank."""
        val : float = 0.0
        val += sum(o.get_load() for o in self.__migratable_objects)
        return val

    @qoi
    def get_sentinel_load(self) -> float:
        """Return sentinel load on rank."""
        val : float = 0.0
        val += sum(o.get_load() for o in self.__sentinel_objects)
        return val

    @qoi
    def get_received_volume(self) -> float:
        """Return volume received by objects assigned to rank from other ranks."""
        # Iterate over all objects assigned to rank
        volume : float = 0.0
        obj_set = self.__migratable_objects.union(self.__sentinel_objects)
        for o in obj_set:
            # Skip objects without communication
            if not o.has_communicator():
                continue

            # Add total volume received from non-local objects
            volume += sum(v for k, v in o.get_communicator().get_received().items() if k not in obj_set)

        # Return computed volume
        return volume

    @qoi
    def get_sent_volume(self) -> float:
        """Return volume sent by objects assigned to rank to other ranks."""
        # Iterate over all objects assigned to rank
        volume = 0.0
        obj_set = self.__migratable_objects.union(self.__sentinel_objects)
        for o in obj_set:
            # Skip objects without communication
            if not o.has_communicator():
                continue

            # Add total volume sent to non-local objects
            volume += sum(
                v for k, v in o.get_communicator().get_sent().items()
                if k not in obj_set)

        # Return computed volume
        return volume

    @qoi
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

    @qoi
    def get_max_memory_usage(self) -> float:
        """Return maximum memory usage on rank."""
        return self.__size + self.get_shared_memory() + self.get_max_object_level_memory()

    def get_qois(self) -> list:
        """Get all methods decorated with the QOI decorator.
        """
        qoi_methods : dict = {
            name: getattr(self, name)
            for name in dir(self)
            if callable(getattr(self, name)) and not name.startswith("__") and hasattr(getattr(self, name), "is_qoi") }
        return qoi_methods
