###############################################################################
#
#                       lbsAffineCombinationWorkModel.py
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
from logging import Logger

from src.Model.lbsWorkModelBase import WorkModelBase
from src.Model.lbsRank import Rank


class AffineCombinationWorkModel(WorkModelBase):
    """A concrete class for a load-only work model
    """

    def __init__(self, parameters, lgr: Logger = None):
        """Class constructor:
        parameters: dictionary with alpha, beta, and gamma values
        """
        # Assign logger to instance variable
        self.lgr = lgr

        # Use default values if parameters not provided
        self.alpha = parameters.get("alpha", 1.)
        self.beta = parameters.get("beta", 0.)
        self.gamma = parameters.get("gamma", 0.)

        # Call superclass init
        super(AffineCombinationWorkModel, self).__init__(parameters)
        self.lgr.info(f"Instantiated work model with alpha={self.alpha}, beta={self.beta}, gamma={self.gamma}")

    def compute(self, rank: Rank):
        """A work model with affine combination of load and communication
        alpha * load + beta * max(sent, received) + gamma
        """
        # Compute affine combination of load and volumes
        return self.alpha * rank.get_load() + self.beta * max(
            rank.get_received_volume(),
            rank.get_sent_volume()) + self.gamma

    def aggregate(self, values: dict):
        """A work model with affine combination of load and communication
        alpha * load + beta * max(sent, received) + gamma
        """

        # Return work using provided values
        return self.alpha * values.get("load", 0.) + self.beta * max(
            values.get("received volume", 0.),
            values.get("sent volume", 0.)) + self.gamma
