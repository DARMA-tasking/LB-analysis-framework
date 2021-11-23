###############################################################################
#
#                       lbsRelaxedLocalizingCriterion.py
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
import functools
import sys

import bcolors

from src.Execution.lbsCriterionBase import CriterionBase
from src.Model.lbsObjectCommunicator import ObjectCommunicator


class RelaxedLocalizingCriterion(CriterionBase):
    """A concrete class for a relaxedly localizing criterion
    """

    def __init__(self, processors, edges, _):
        """Class constructor:
        processors: set of processors (lbsRank.Rank instances)
        edges: dictionary of edges (frozensets)
        _: no parameters dictionary needed for this criterion
        """

        # Call superclass init
        super(RelaxedLocalizingCriterion, self).__init__(processors, edges)
        print(bcolors.HEADER
            + "[RelaxedLocalizingCriterion] "
            + bcolors.END
            + "Instantiated concrete criterion")

    def compute(self, object, p_src, p_dst):
        """A criterion allowing for local disruptions for more locality
        """

        # Retrieve object communications
        comm = object.get_communicator()
        if not isinstance(comm, ObjectCommunicator):
            print(f"{bcolors.ERR}[RelaxedLocalizingCriterion] No ObjectCommunicator provided!. {comm} object of type "
                  f"{type(comm)} was provided. Quitting ...{bcolors.END}")
            sys.exit(1)
        sent = comm.get_sent().items()
        recv = comm.get_received().items()

        # Retrieve ID of processor to which an object is assigned
        p_id = (lambda x: x.get_processor_id())

        # Test whether first component is source processor
        is_s = (lambda x: p_id(x[0]) == p_src.get_id())

        # Test whether first component is destination processor
        is_d = (lambda x: p_id(x[0]) == p_dst.get_id())

        # Add value with second components of a collection
        xPy1 = (lambda x, y: x + y[1])

        # Aggregate communication weights with source
        w_src = functools.reduce(xPy1,
                                 list(filter(is_s, recv))
                                 + list(filter(is_s, sent)),
                                 0.)

        # Aggregate communication weights with destination
        w_dst = functools.reduce(xPy1,
                                 list(filter(is_d, recv))
                                 + list(filter(is_d, sent)),
                                 0.)

        # Criterion assesses difference in local communications
        return w_dst - w_src
