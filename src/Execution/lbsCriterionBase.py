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
lbsCriterionBase_module_aliases = {}
for m in [
    "abc"
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsCriterionBase_module_aliases:
            globals()[lbsCriterionBase_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Model import lbsProcessor, lbsObject

########################################################################
class CriterionBase:
    __metaclass__ = abc.ABCMeta
    """An abstract base class of optimization criteria for LBS execution
    """

    ####################################################################
    def __init__(self, processors, edges, parameters=None):
        """Class constructor:
        processors: set of processors (lbsProcessor.Processor instances)
        edges: dictionary of edges (frozensets)
        parameters: optional parameters dictionary
        """

        # If no list of processors was was provided, do not do anything
        if not isinstance(processors, set):
            print("** ERROR: Could not create a LBS criterion without a set of processors")
            return

        # Assert that all members of said list are indeed processor instances
        n_p = len(processors)
        if n_p != len(
            filter(lambda x: isinstance(x, lbsProcessor.Processor), processors)):
            print("** ERROR: Could not create a LBS criterion without a set of Processor instances")
            return
            
        # If no dictionary of edges was was provided, do not do anything
        if not isinstance(edges, dict):
            print("** ERROR: Could not create a LBS criterion without a dictionary of edges")
            return

        # Assert that all members of said dictionary are indeed frozen sets
        n_e = len(edges)
        if n_e != len(
            filter(lambda x: isinstance(x, frozenset), edges)):
            print("** ERROR: Could not create a LBS criterion without a dictionary of frozen sets")
            return

        # Criterion keeps internal references to processors and edges
        self.processors = processors
        self.edges = edges
        print("[CriterionBase] Assigned {} processors and {} edges to base criterion".format(
            n_p,
            n_e))

    ####################################################################
    @abc.abstractmethod
    def compute(self, object, proc_src, proc_dst):
        """Return value of criterion for candidate object transfer
        """

        # Must be implemented by concrete subclass
        pass
    
########################################################################
