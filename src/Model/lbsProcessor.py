#
#@HEADER
###############################################################################
#
#                                lbsProcessor.py
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

from src.Model.lbsMessage import Message


class Processor:
    """A class representing a processor to which objects are assigned
    """

    def __init__(self, i, o=set()):
        # Member variables passed by constructor
        self.index = i
        self.objects = set()
        for obj in o:
            self.add_object(obj)

        # No information about underloads is known initially
        self.known_underloaded = set()
        self.known_underloads = {}

        # No overloaded viewers exist initially
        self.overloaded_viewers = set()

        # No message was received initially
        self.round_last_received = 0

    def get_id(self):
        """Return processor ID
        """

        return self.index

    def get_objects(self):
        """Return objects assigned to processor
        """

        return self.objects

    def get_object_ids(self):
        """Return IDs of objects assigned to processor
        """

        return [o.get_id() for o in self.objects]

    def get_known_underloaded(self):
        """Return underloaded peers know to self
        """

        return self.known_underloaded

    def get_known_underloads(self):
        """Return underloads peers know to self
        """

        return self.known_underloads

    def get_overloaded_viewers(self):
        """Return overloaded peers knowing about self
        """

        return self.overloaded_viewers

    def add_object(self, o, l_ave=None):
        """Assign object to self
        """

        # Add object from those assigned to self
        self.objects.add(o)

        # Check whether addition makes load above underload threshold
        if l_ave and not sum([o.get_time() for o in self.objects]) < l_ave:
            # Remove self from underloaded when present
            self.known_underloaded.discard(self)
            self.known_underloads.pop(self, None)

    def remove_object(self, o, p_dst):
        """Remove from self object sent to peer
        """

        # Remove object from those assigned to self
        self.objects.remove(o)

        # Update known underloads
        l_o = o.get_time()
        l_dst = self.known_underloads[p_dst]
        if l_dst + l_o > sum([o.get_time() for o in self.objects]):
            # Remove destination from underloaded if more loaded than self
            self.known_underloaded.remove(p_dst)
            del self.known_underloads[p_dst]
        else:
            # Update load
            self.known_underloads[p_dst] += l_o

        # Return removed object time
        return l_o
        
    def add_as_overloaded_viewer(self, underloaded_processors):
        """Add self as viewer to underloaded peers
        """

        # Add self as viewer of each of provided underloaded processors
        for p in underloaded_processors:
            p.overloaded_viewers.add(self)

    def get_known_underload(self, p):
        """Return known peer underload when available or infinity
        """

        return self.known_underloads.get(p, math.inf)

    def get_load(self):
        """Return computed total load on processor
        """

        return sum([o.get_time() for o in self.objects])

    def reset_all_load_information(self):
        """Reset all underload information known to self
        """

        # Reset information about known underloaded peers
        self.known_underloaded = set()
        self.known_underloads = {}

        # Reset information about overloaded viwewer peers
        self.overloaded_viewers = set()

    def initialize_underloads(self, procs, l_ave, f):
        """Initialize underloads when needed to sample of selected peers
        """

        # Retrieve current load on this processor
        l = self.get_load()

        # Return empty underload information if processor not underloaded
        if not l < l_ave:
            return [], None
            
        # Make underloaded processor aware of being underloaded
        self.known_underloaded = set([self])
        self.known_underloads[self] = l

        # Create underload message tagged at first round
        msg = Message(1, (self.known_underloaded, self.known_underloads))

        # Broadcast underloads to pseudo-random sample of procs excluding self
        return rnd.sample(procs.difference([self]), min(f, len(procs) - 1)), msg

    def forward_underloads(self, r, procs, f):
        """Formard underloads to sample of selected peers
        """

        # Compute complement of set of underloaded processors
        c_procs = procs.difference(self.known_underloaded).difference([self])

        # Create underload message tagged at current round
        msg = Message(r, (self.known_underloaded, self.known_underloads))

        # Forward underloads to pseudo-random sample of procs
        return rnd.sample(c_procs, min(f, len(c_procs))), msg

    def process_underload_message(self, msg):
        """Update internals when underload message is received
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

        # Union received set of underloaded procs with current one
        self.known_underloaded.update(info[0])

        # Update underload information
        self.known_underloads.update(info[1])

        # Sanity check
        l1 = len(self.known_underloaded)
        l2 = len(self.known_underloads)
        if l1 != l2:
            print(bcolors.ERR
                  + "** ERROR: cannot process message at processor {}: {}<>{}. Exiting.".format(
                      self.get_id(),
                      l1,
                      l2)
                  + bcolors.END)
            sys.exit(1)

        # Update last received message index
        self.round_last_received = msg.get_round()

    def compute_cmf_underloads(self, l_ave, pmf_type=0):
        """Compute CMF of underloads given an average load
           type 0: improved Gossip approach
           type 1: NS variant based on sender load
        """

        # Initialize CMF
        sum_p = 0
        cmf = []
        p_fac = 1

        # Retrieve known underloads
        loads = self.known_underloads.values()
        
        # Distinguish between different PMF types
        if not pmf_type:
            # Determine whether one underloaded is actually overloaded
            l_max = max(loads)
            p_fac /= (l_max if l_max > l_ave else l_ave)

        elif pmf_type == 1:
            # User sender load
            p_fac /= self.get_load()
            
        else:
            print(f"{bcolors.ERR}** ERROR: unsupported PMF type: {pmf_type}. Exiting.{bcolors.END}")
            sys.exit(1)

        # Compute CMF over all loads
        for l in loads:
            sum_p += 1 - p_fac * l
            cmf.append(sum_p)

        # Normalize and return CMF
        return [x / sum_p for x in cmf]
