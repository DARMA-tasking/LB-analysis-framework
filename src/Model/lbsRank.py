#
#@HEADER
###############################################################################
#
#                                lbsRank.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
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
from logging import Logger
import random as rnd
import sys

from src.Model.lbsMessage import Message
from utils.logger import CLRS


class Rank:
    """A class representing a rank to which objects are assigned
    """

    def __init__(self, i, mo: set = None, so: set = None, logger: Logger = None):
        # Assign logger to instance variable
        self.lgr = logger
        # Assign colors for logger
        self.grn = CLRS.get('green')
        self.red = CLRS.get('red')
        self.ylw = CLRS.get('yellow')
        self.cyan = CLRS.get('cyan')

        # Member variables passed by constructor
        self.index = i
        self.migratable_objects = set()
        if mo is not None:
            for o in mo:
                self.migratable_objects.add(o)
        self.sentinel_objects = set()
        if so is not None:
            for o in so:
                self.sentinel_objects.add(o)

        # No information about peers is known initially
        self.known_ranks = set()
        self.known_loads = {}

        # No viewers exist initially
        self.viewers = set()

        # No message was received initially
        self.round_last_received = 0

    def __repr__(self):
        return f"<Rank index: {self.index}>"

    def get_id(self):
        """Return rank ID
        """
        return self.index

    def get_objects(self):
        """Return all objects assigned to rank
        """
        return self.migratable_objects.union(self.sentinel_objects)

    def add_migratable_object(self, o):
        """Add object to migratable objects
        """
        return self.migratable_objects.add(o)

    def get_migratable_objects(self):
        """Return migratable objects assigned to rank
        """
        return self.migratable_objects

    def get_sentinel_objects(self):
        """Return sentinel objects assigned to rank
        """
        return self.sentinel_objects

    def get_object_ids(self):
        """Return IDs of all objects assigned to rank
        """
        return [o.get_id() for o in self.migratable_objects.union(self.sentinel_objects)]

    def get_migratable_object_ids(self):
        """Return IDs of migratable objects assigned to rank
        """
        return [o.get_id() for o in self.migratable_objects]

    def get_sentinel_object_ids(self):
        """Return IDs of sentinel objects assigned to rank
        """
        return [o.get_id() for o in self.sentinel_objects]

    def get_known_ranks(self):
        """Return peers know to self
        """
        return self.known_ranks

    def get_known_loads(self):
        """Return loads of peers know to self
        """
        return self.known_loads

    def get_viewers(self):
        """Return peers knowing about self
        """
        return self.viewers

    def remove_migratable_object(self, o, p_dst, work_model):
        """Remove migratable able object from self object sent to peer
        """
        # Remove object from those assigned to self
        self.migratable_objects.remove(o)

        # Update known loads
        l_o = o.get_time()
        l_dst = self.known_loads[p_dst]
        if l_dst + l_o > self.get_load():
            # Remove destination from known loads if more loaded than self
            self.known_ranks.remove(p_dst)
            del self.known_loads[p_dst]
        else:
            # Update loads
            self.known_loads[p_dst] += l_o

        # Return removed object load
        return l_o
        
    def add_as_viewer(self, ranks):
        """Add self as viewer to known peers
        """
        # Add self as viewer of each of provided ranks
        for p in ranks:
            p.viewers.add(self)

    def get_load(self):
        """Return total load on rank
        """
        return sum([o.get_time() for o in self.migratable_objects.union(self.sentinel_objects)])

    def get_migratable_load(self):
        """Return migratable load on rank
        """
        return sum([o.get_time() for o in self.migratable_objects])

    def get_sentinel_load(self):
        """Return sentinel load oon rank
        """
        return sum([o.get_time() for o in self.sentinel_objects])

    def get_received_volume(self):
        """Return volume received by objects assigned to rank from other ranks
        """
        # Iterate over all objects assigned to rank
        volume = 0
        obj_set = self.migratable_objects.union(self.sentinel_objects)
        for o in obj_set:
            # Skip objects without communication
            if not o.has_communicator():
                continue

            # Add total volume received from non-local objects
            volume += sum([v for k, v in o.get_communicator().get_received().items() if k not in obj_set])

        # Return computed volume
        return volume    

    def get_sent_volume(self):
        """Return volume sent by objects assigned to rank to other ranks
        """
        # Iterate over all objects assigned to rank
        volume = 0
        obj_set = self.migratable_objects.union(self.sentinel_objects)
        for o in obj_set:
            # Skip objects without communication
            if not o.has_communicator():
                continue

            # Add total volume sent to non-local objects
            volume += sum([v for k, v in o.get_communicator().get_sent().items() if k not in obj_set])

        # Return computed volume
        return volume    

    def reset_all_load_information(self):
        """Reset all load information known to self
        """
        # Reset information about known loaded peers
        self.known_ranks = set()
        self.known_loads = {}

        # Reset information about overloaded viwewer peers
        self.viewers = set()

    def initialize_message(self, ranks, f):
        """Initialize maessage to be sent to selected peers
        """
        # Retrieve current load on this rank
        l = self.get_load()

        # Make rank aware of own load
        self.known_ranks = set([self])
        self.known_loads[self] = l

        # Create load message tagged at first round
        msg = Message(1, (self.known_ranks, self.known_loads))

        # Broadcast message to pseudo-random sample of ranks excluding self
        return rnd.sample(ranks.difference(
            [self]), min(f, len(ranks) - 1)), msg

    def forward_message(self, r, ranks, f):
        """Formard information message to sample of selected peers
        """
        # Compute complement of set of known peers

        c_ranks = ranks.difference(self.known_ranks).difference([self])

        # Create load message tagged at current round
        msg = Message(r, (self.known_ranks, self.known_loads))

        # Forward message to pseudo-random sample of ranks
        return rnd.sample(c_ranks, min(f, len(c_ranks))), msg

    def process_message(self, msg):
        """Update internals when message is received
        """
        # Assert that message has the expected type
        if not isinstance(msg, Message):
            self.lgr.debug(self.cyan(f"Attempted to pass message of incorrect type {type(msg)}. Ignoring it."))

        # Retrieve information from message
        info = msg.get_content()
        if len(info) < 2:
            self.lgr.debug(self.cyan(f"Incomplete message content: {info}. Ignoring it."))
            return

        # Union received set of loaded ranks with current one
        self.known_ranks.update(info[0])

        # Update load information
        self.known_loads.update(info[1])

        # Sanity check
        l1 = len(self.known_ranks)
        l2 = len(self.known_loads)
        if l1 != l2:
            self.lgr.error(self.red(f"Cannot process message at rank {self.get_id()}: {l1}<>{l2}. Exiting."))
            sys.exit(1)

        # Update last received message index
        self.round_last_received = msg.get_round()

    def compute_transfer_cmf(self):
        """Compute CMF for the sampling of transfer targets
        """
        # Initialize CMF
        sum_p = 0
        cmf = []

        # Retrieve known loads
        loads = self.known_loads.values()
        
        # Normalize with respect to maximum load
        p_fac = 1. / max(loads)

        # Compute CMF over all known ranks
        for l, p in zip(loads, self.known_ranks):
            # Self does not contribute to CMF
            if p.get_id() != self.index:
                sum_p += 1 - p_fac * l
            cmf.append(sum_p)

        # Normalize and return CMF
        return [x / sum_p for x in cmf] if sum_p else None
