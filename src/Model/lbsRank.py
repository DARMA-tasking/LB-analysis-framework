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
import math
import random as rnd
import sys
import bcolors

from src.Model.lbsObject import Object
from src.Model.lbsMessage import Message


class Rank:
    """A class representing a rank to which objects are assigned
    """

    def __init__(self, i, mo: set = None, so: set = None):
        # Member variables passed by constructor
        self.index = i
        self.migratable_objects = set()
        self.sentinel_objects = set()
        if mo is not None:
            for o in mo:
                self.migratable_objects.add(o)
        if so is not None:
            for o in so:
                self.sentinel_objects.add(o)

        # No information about loads is known initially
        self.known_loaded = set()
        self.known_loads = {}

        # No viewers exist initially
        self.viewers = set()

        # No message was received initially
        self.round_last_received = 0

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

    def get_known_loaded(self):
        """Return peers whose load is know to self
        """

        return self.known_loaded

    def get_known_loads(self):
        """Return loads of peers know to self
        """

        return self.known_loads

    def get_viewers(self):
        """Return peers knowing about self
        """

        return self.viewers

    def remove_migratable_object(self, o, p_dst):
        """Remove migratable able object from self object sent to peer
        """

        # Remove object from those assigned to self
        self.migratable_objects.remove(o)

        # Update known loads
        l_o = o.get_time()
        l_dst = self.known_loads[p_dst]
        if l_dst + l_o > self.get_load():
            # Remove destination from known loads if more loaded than self
            self.known_loaded.remove(p_dst)
            del self.known_loads[p_dst]
        else:
            # Update load
            self.known_loads[p_dst] += l_o

        # Return removed object time
        return l_o
        
    def add_as_viewer(self, ranks):
        """Add self as viewer to known peers
        """

        # Add self as viewer of each of provided ranks
        for p in ranks:
            p.viewers.add(self)

    def get_known_load(self, p):
        """Return known peer load when available or infinity
        """

        return self.known_loads.get(p, math.inf)

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

    def reset_all_load_information(self):
        """Reset all load information known to self
        """

        # Reset information about known loaded peers
        self.known_loaded = set()
        self.known_loads = {}

        # Reset information about overloaded viwewer peers
        self.viewers = set()

    def initialize_loads(self, procs, f):
        """Initialize loads when needed to sample of selected peers
        """

        # Retrieve current load on this rank
        l = self.get_load()

        # Make rank aware of own load
        self.known_loaded = set([self])
        self.known_loads[self] = l

        # Create load message tagged at first round
        msg = Message(1, (self.known_loaded, self.known_loads))

        # Broadcast loads to pseudo-random sample of procs excluding self
        return rnd.sample(procs.difference([self]), min(f, len(procs) - 1)), msg

    def forward_loads(self, r, procs, f):
        """Formard loads to sample of selected peers
        """

        # Compute complement of set of known rank loads
        c_procs = procs.difference(self.known_loaded).difference([self])

        # Create load message tagged at current round
        msg = Message(r, (self.known_loaded, self.known_loads))

        # Forward loads to pseudo-random sample of procs
        return rnd.sample(c_procs, min(f, len(c_procs))), msg

    def process_load_message(self, msg):
        """Update internals when load message is received
        """

        # Assert that message has the expected type
        if not isinstance(msg, Message):
            print(bcolors.WARN
                + "*  WARNING: attempted to pass message of incorrect type {}. Ignoring it.".format(
                type(msg))
                + bcolors.END)

        # Retrieve information from message
        info = msg.get_content()
        if len(info) < 2:
            print(bcolors.WARN
                + "*  WARNING: incomplete message content: {}. Ignoring it.".format(
                info)
                + bcolors.END)
            return

        # Union received set of loaded procs with current one
        self.known_loaded.update(info[0])

        # Update load information
        self.known_loads.update(info[1])

        # Sanity check
        l1 = len(self.known_loaded)
        l2 = len(self.known_loads)
        if l1 != l2:
            print(bcolors.ERR
                  + "** ERROR: cannot process message at rank {}: {}<>{}. Exiting.".format(
                      self.get_id(),
                      l1,
                      l2)
                  + bcolors.END)
            sys.exit(1)

        # Update last received message index
        self.round_last_received = msg.get_round()

    def compute_cmf_loads(self):
        """Compute CMF of loads
        """

        # Initialize CMF
        sum_p = 0
        cmf = []

        # Retrieve known loads
        loads = self.known_loads.values()
        
        # Normalize with respect to maximum load
        p_fac = 1. / max(loads)

        # Compute CMF over all known ranks
        for l, p in zip(loads, self.known_loaded):
            # Self does not contribute to CMF
            if p.get_id() != self.index:
                sum_p += 1 - p_fac * l
            cmf.append(sum_p)

        # Normalize and return CMF
        return [x / sum_p for x in cmf] if sum_p else None
