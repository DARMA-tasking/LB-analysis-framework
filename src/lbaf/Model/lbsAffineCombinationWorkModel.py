#
#@HEADER
###############################################################################
#
#                       lbsAffineCombinationWorkModel.py
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
import math
from logging import Logger

from .lbsWorkModelBase import WorkModelBase
from .lbsRank import Rank
from .lbsNode import Node


class AffineCombinationWorkModel(WorkModelBase):
    """A concrete class for a load-only work model"""

    def __init__(self, parameters, lgr: Logger):
        """Class constructor:

        parameters: dictionary with alpha, beta, gamma and delta values.
        """
        # Assign logger to instance variable
        self.__logger = lgr

        # Use default values if parameters not provided
        self.__beta = parameters.get("beta", 0.0)
        self.__gamma = parameters.get("gamma", 0.0)
        self.__delta = parameters.get("delta", 0.0)
        self.__upper_bounds = parameters.get("upper_bounds", {})
        self.__node_bounds = parameters.get("node_bounds", False)

        # Call superclass init
        super().__init__(parameters)
        self.__logger.info(
            "Instantiated work model with: "
            f"beta={self.__beta}, gamma={self.__gamma}, delta={self.__delta}")
        for k, v in self.__upper_bounds.items():
            self.__logger.info(
                f"Upper bound for {'node' if self.__node_bounds else 'rank'} {k}: {v}")

    def get_beta(self):
        """Get the beta parameter."""
        return self.__beta

    def get_gamma(self):
        """Get the gamma parameter."""
        return self.__gamma

    def get_delta(self):
        """Get the delta parameter."""
        return self.__delta

    def affine_combination(self, a, l, v1, v2, h):
        """Compute affine combination of load, maximum volume, and homing cost."""
        return a * l + self.__beta * max(v1, v2) + self.__gamma + self.__delta * h

    def compute(self, rank: Rank):
        """A work model with affine combination of load and communication.
        alpha * load + beta * max(sent, received) + gamma + delta * homing,
        under optional strict upper bounds.
        """
        # Check whether strict bounds are satisfied
        for k, v in self.__upper_bounds.items():
            if getattr(
                    rank.get_node() if self.__node_bounds else rank,
                    f"get_{k}")() > v:
                return math.inf

        # Return combination of load and volumes
        return self.affine_combination(
            rank.get_alpha(),
            rank.get_load(),
            rank.get_received_volume(),
            rank.get_sent_volume(),
            rank.get_homing())

    def __update_load(self, rank: Rank, o_snd: list, o_rcv: list):
        """Update total load if objects are to be sent and received."""
        return rank.get_load() - sum(
            o.get_load() for o in o_snd) + sum(
                o.get_load() for o in o_rcv)

    def __update_received(self, rank: Rank, o_snd: list, o_rcv: list):
        """Update received volume if objects are to be sent and received."""
        # Keep track of rank id and objects
        r_id = rank.get_id()
        r_obj = rank.get_objects().copy()

        # Retrieve current received volume
        volume = rank.get_received_volume()

        # Iterate over all sent objects
        for o in o_snd:
            # Skip non-communicating objects
            if not (c := o.get_communicator()):
                continue

            # Subtract communications received by object from other ranks
            for k, v in c.get_received().items():
                if k not in r_obj:
                    volume -= v

            # Add communications sent from object to current rank
            for k, v in c.get_sent().items():
                if k in r_obj:
                    volume += v

            # Remove object from rank
            r_obj.discard(o)
            
        # Iterate over all received objects
        for o in o_rcv:
            # Skip non-communicating objects
            if not (c := o.get_communicator()):
                continue

            # Add communications received by object from other ranks
            for k, v in c.get_received().items():
                if k not in r_obj:
                    volume += v

            # Subtract communications sent from object to current rank
            for k, v in c.get_sent().items():
                if k in r_obj:
                    volume -= v

            # Add object to rank
            r_obj.add(o)
            
        # Return updated received volume
        return volume

    def __update_sent(self, rank: Rank, o_snd: list, o_rcv: list):
        """Update sent volume if objects are to be sent and received."""
        # Keep track of rank id and objects
        r_id = rank.get_id()
        r_obj = rank.get_objects().copy()

        # Retrieve current sent volume
        volume = rank.get_sent_volume()

        # Iterate over all sent objects
        for o in o_snd:
            # Skip non-communicating objects
            if not (c := o.get_communicator()):
                continue

            # Subtract communications sent from object to other ranks
            for k, v in c.get_sent().items():
                if k not in r_obj:
                    volume -= v

            # Add communications received by object from current rank
            for k, v in c.get_received().items():
                if k in r_obj:
                    volume += v

            # Remove object from rank
            r_obj.discard(o)
            
        # Iterate over all received objects
        for o in o_rcv:
            # Skip non-communicating objects
            if not (c := o.get_communicator()):
                continue

            # Add communications sent from object to other ranks
            for k, v in c.get_sent().items():
                if k not in r_obj:
                    volume += v

            # Subtract communications received by object from current rank
            for k, v in c.get_received().items():
                if k in r_obj:
                    volume -= v

            # Add object to rank
            r_obj.add(o)
            
        # Return updated sent volume
        return volume

    def __update_homing(self, rank: Rank, o_snd: list, o_rcv: list):
        """Update homing costs if objects are to be sent and received."""
        # Keep track of rank id and objects
        r_id = rank.get_id()
        r_obj = rank.get_objects().copy()

        # Retrieve current homing cost
        homing = rank.get_homing()

        # Iterate over all sent objects
        for o in o_snd:
            # Remove object from rank
            r_obj.discard(o)

            # Skip locally homed blocks
            b = o.get_shared_block()
            if b.get_home_id() == r_id:
                continue

            # Determine set of removed non-homed blocks
            S = set({b})
            for o_oth in r_obj:
                if o_oth.get_shared_block() == b:
                    S = set()
                    break

            # Update homing cost
            for b in S:
                homing -= b.get_size()

        # Iterate over all received objects
        for o in o_rcv:
            # Skip locally homed blocks
            b = o.get_shared_block()
            if b.get_home_id() == r_id:
                continue

            # Determine set of added non-homed blocks
            S = set({b})
            for o_oth in r_obj:
                if o_oth.get_shared_block() == b:
                    S = set()
                    break

            # Update homing cost
            for b in S:
                homing += b.get_size()

            # Addd object to rank
            r_obj.add(o)

        # Return updated homing cost
        return homing

    def update(self, rank: Rank, o_snd: list, o_rcv: list):
        """Update work if objects are to be sent and received."""
        # Return combination of load and volumes
        return self.affine_combination(
            rank.get_alpha(),
            self.__update_load(rank, o_snd, o_rcv),
            self.__update_received(rank, o_snd, o_rcv),
            self.__update_sent(rank, o_snd, o_rcv),
            self.__update_homing(rank, o_snd, o_rcv))
