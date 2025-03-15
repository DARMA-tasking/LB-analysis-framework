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

        parameters: dictionary with alpha, beta, and gamma values.
        """
        # Assign logger to instance variable
        self.__logger = lgr

        # Use default values if parameters not provided
        self.__beta = parameters.get("beta", 0.0)
        self.__gamma = parameters.get("gamma", 0.0)
        self.__upper_bounds = parameters.get("upper_bounds", {})
        self.__node_bounds = parameters.get("node_bounds", False)

        # Call superclass init
        super().__init__(parameters)
        self.__logger.info(
            "Instantiated work model with: "
            f"beta={self.__beta}, gamma={self.__gamma}")
        for k, v in self.__upper_bounds.items():
            self.__logger.info(
                f"Upper bound for {'node' if self.__node_bounds else 'rank'} {k}: {v}")

    def get_beta(self):
        """Get the beta parameter."""
        return self.__beta

    def get_gamma(self):
        """Get the gamma parameter."""
        return self.__gamma

    def affine_combination(self, a, l, v1, v2):
        """Compute affine combination of load and maximum volume."""
        print(a, l, v1, v2, "-->", a * l + self.__beta * max(v1, v2) + self.__gamma)
        return a * l + self.__beta * max(v1, v2) + self.__gamma

    def compute(self, rank: Rank):
        """A work model with affine combination of load and communication.

        alpha * load + beta * max(sent, received) + gamma,
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
            rank.get_sent_volume())
