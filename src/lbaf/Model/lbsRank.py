from logging import Logger
import random as rnd
import math

from .lbsMessage import Message


class Rank:
    """ A class representing a rank to which objects are assigned
    """

    def __init__(self, i: int, logger: Logger, mo: set = None, so: set = None):
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

        # No information about peers is known initially
        self.__known_loads = {}

        # No viewers exist initially
        self.__viewers = set()

        # No message was received initially
        self.round_last_received = 0

    def __repr__(self):
        return f"<Rank index: {self.__index}>"

    def get_id(self) -> int:
        """ Return rank ID
        """
        return self.__index

    def get_objects(self) -> set:
        """ Return all objects assigned to rank
        """
        return self.__migratable_objects.union(self.__sentinel_objects)

    def add_migratable_object(self, o) -> None:
        """ Add object to migratable objects
        """
        return self.__migratable_objects.add(o)

    def get_migratable_objects(self) -> set:
        """ Return migratable objects assigned to rank
        """
        return self.__migratable_objects

    def get_sentinel_objects(self) -> set:
        """ Return sentinel objects assigned to rank
        """
        return self.__sentinel_objects

    def get_object_ids(self) -> list:
        """ Return IDs of all objects assigned to rank
        """
        return [o.get_id() for o in self.__migratable_objects.union(self.__sentinel_objects)]

    def get_migratable_object_ids(self) -> list:
        """ Return IDs of migratable objects assigned to rank
        """
        return [o.get_id() for o in self.__migratable_objects]

    def get_sentinel_object_ids(self) -> list:
        """ Return IDs of sentinel objects assigned to rank
        """
        return [o.get_id() for o in self.__sentinel_objects]

    def get_known_loads(self) -> dict:
        """ Return loads of peers know to self
        """
        return self.__known_loads

    def get_viewers(self) -> set:
        """ Return peers knowing about self
        """
        return self.__viewers

    def remove_migratable_object(self, o, p_dst):
        """ Remove migratable able object from self object sent to peer
        """
        # Remove object from those assigned to self
        self.__migratable_objects.remove(o)

        # Update known loads when these exist
        if self.__known_loads:
            self.__known_loads[p_dst] += o.get_time()
        
    def add_as_viewer(self, ranks):
        """ Add self as viewer to known peers
        """
        # Add self as viewer of each of provided ranks
        for p in ranks:
            p.__viewers.add(self)

    def get_load(self) -> float:
        """ Return total load on rank
        """
        return sum([o.get_time() for o in self.__migratable_objects.union(self.__sentinel_objects)])

    def get_migratable_load(self) -> float:
        """ Return migratable load on rank
        """
        return sum([o.get_time() for o in self.__migratable_objects])

    def get_sentinel_load(self) -> float:
        """ Return sentinel load oon rank
        """
        return sum([o.get_time() for o in self.__sentinel_objects])

    def get_received_volume(self):
        """ Return volume received by objects assigned to rank from other ranks
        """
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
        """ Return volume sent by objects assigned to rank to other ranks
        """
        # Iterate over all objects assigned to rank
        volume = 0
        obj_set = self.__migratable_objects.union(self.__sentinel_objects)
        for o in obj_set:
            # Skip objects without communication
            if not o.has_communicator():
                continue

            # Add total volume sent to non-local objects
            volume += sum([v for k, v in o.get_communicator().get_sent().items() if k not in obj_set])

        # Return computed volume
        return volume    

    def reset_all_load_information(self):
        """ Reset all load information known to self
        """
        # Reset information about known peers
        self.__known_loads = {}

        # Reset information about overloaded viewer peers
        self.__viewers = set()

    def initialize_message(self, loads, f):
        """ Initialize message to be sent to selected peers
        """
        # Retrieve current load on this rank
        l = self.get_load()

        # Make rank aware of own load
        self.__known_loads[self] = l

        # Create load message tagged at first round
        msg = Message(1, self.__known_loads)

        # Broadcast message to pseudo-random sample of ranks excluding self
        return rnd.sample(set(loads).difference([self]), min(f, len(loads) - 1)), msg

    def forward_message(self, r, s, f):
        """ Forward information message to sample of selected peers
        """
        # Create load message tagged at current round
        msg = Message(r, self.__known_loads)

        # Compute complement of set of known peers
        complement = set(
            self.__known_loads).difference([self])

        # Forward message to pseudo-random sample of ranks
        return rnd.sample(
            complement, min(f, len(complement))), msg

    def process_message(self, msg):
        """ Update internals when message is received
        """
        # Assert that message has the expected type
        if not isinstance(msg, Message):
            self.__logger.warning(f"Attempted to pass message of incorrect type {type(msg)}. Ignoring it.")

        # Update load information
        self.__known_loads.update(msg.get_content())

        # Update last received message index
        self.round_last_received = msg.get_round()

    def compute_transfer_cmf(self, transfer_criterion, o, targets, strict=False):
        """ Compute CMF for the sampling of transfer targets
        """
        # Initialize criterion values
        c_values = {}
        c_min, c_max = math.inf, -math.inf

        # Iterate over potential targets
        for p_dst in targets.keys():
            # Compute value of criterion for current target
            c = transfer_criterion.compute([o], self, p_dst)

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
