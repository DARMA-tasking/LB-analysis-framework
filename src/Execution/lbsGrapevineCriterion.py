#
#@HEADER
###############################################################################
#
#                           lbsGrapevineCriterion.py
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
lbsGrapevineCriterion_module_aliases = {}
for m in [
    "bcolors",
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsGrapevineCriterion_module_aliases:
            globals()[lbsGrapevineCriterion_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Execution.lbsCriterionBase   import CriterionBase

########################################################################
class GrapevineCriterion(CriterionBase):
    """A concrete class for the original Grapevine criterion
    """

    ####################################################################
    def __init__(self, processors, edges, parameters):
        """Class constructor:
        processors: set of processors (lbsProcessor.Processor instances)
        edges: dictionary of edges (frozensets)
        parameters: optional parameters dictionary
            average_load: average load across all processors
        """

        # Call superclass init
        super(GrapevineCriterion, self).__init__(processors, edges, parameters)

        # Keep track of average load across all processors
        key = "average_load"
        ave_load =  parameters.get(key)
        if ave_load:
            self.average_load = ave_load
            print(bcolors.HEADER
                + "[GrapevineCriterion] "
                + bcolors.END
                + "Instantiated concrete criterion with average load: {}".format(
            ave_load))
        else:
            print(bcolors.ERR
                + "*  ERROR: cannot instantiate criterion without {} parameter".format(
                key)
                + bcolors.END)

    ####################################################################
    def compute(self, object, _, p_dst):
        """Original Grapevine criterion based on Linfinity norm of loads
        """

        # Criterion only uses object and processor loads
        return self.average_load - (p_dst.get_load() + object.get_time())

########################################################################
