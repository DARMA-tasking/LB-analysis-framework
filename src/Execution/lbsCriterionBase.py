#
#@HEADER
###############################################################################
#
#                              lbsCriterionBase.py
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
########################################################################
import abc

import bcolors

from src.Model.lbsRank import Rank


class CriterionBase:
    __metaclass__ = abc.ABCMeta
    """An abstract base class of optimization criteria for LBS execution
    """

    def __init__(self, ranks, edges, parameters=None):
        """Class constructor:
        ranks: set of ranks (lbsRank.Rank instances)
        edges: dictionary of edges (frozensets)
        parameters: optional parameters dictionary
        """

        # If no list of ranks was was provided, do not do anything
        if not isinstance(ranks, set):
            print(bcolors.ERR
                + "*  ERROR: Could not create a LBS criterion without a set of ranks"
                + bcolors.END)
            return

        # Assert that all members of said list are indeed rank instances
        n_p = len(ranks)
        if n_p != len(list(
            filter(lambda x: isinstance(x, Rank), ranks))):
            print(bcolors.ERR
                + "*  ERROR: Could not create a LBS criterion without a set of Rank instances"
                + bcolors.END)
            return
            
        # If no dictionary of edges was was provided, do not do anything
        if not isinstance(edges, dict):
            print(bcolors.ERR
                + "*  ERROR: Could not create a LBS criterion without a dictionary of edges"
                + bcolors.END)
            return

        # Assert that all members of said dictionary are indeed frozen sets
        n_e = len(edges)
        if n_e != len(list(
            filter(lambda x: isinstance(x, frozenset), edges))):
            print(bcolors.ERR
                + "*  ERROR: Could not create a LBS criterion without a dictionary of frozen sets"
                + bcolors.END)
            return

        # Criterion keeps internal references to ranks and edges
        self.ranks = ranks
        self.edges = edges
        print(bcolors.HEADER
            + "[CriterionBase] "
            + bcolors.END
            + "Assigned {} ranks and {} edges to base criterion".format(
            n_p,
            n_e))

    @staticmethod
    def factory(criterion_idx, ranks, edges, parameters=None):
        """Produce the necessary concrete criterion
        """
        from src.Execution.lbsLowerTotalWorkCriterion import LowerTotalWorkCriterion
        from src.Execution.lbsTemperedLoadCriterion import TemperedLoadCriterion
        from src.Execution.lbsStrictLocalizingCriterion import StrictLocalizingCriterion
        from src.Execution.lbsRelaxedLocalizingCriterion import RelaxedLocalizingCriterion

        # Ensure that criterion index is valid
        c_name = {
            0: LowerTotalWorkCriterion,
            1: TemperedLoadCriterion,
            2: StrictLocalizingCriterion,
            3: RelaxedLocalizingCriterion,
            }.get(criterion_idx)

        # Instantiate and return object
        return c_name(ranks, edges, parameters)

    @abc.abstractmethod
    def compute(self, object, proc_src, proc_dst):
        """Return value of criterion for candidate object transfer
        """

        # Must be implemented by concrete subclass
        pass
