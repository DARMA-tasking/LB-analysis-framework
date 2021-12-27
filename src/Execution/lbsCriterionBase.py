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
import sys
import bcolors

from src.Model.lbsWorkModelBase import WorkModelBase

class CriterionBase:
    __metaclass__ = abc.ABCMeta
    """An abstract base class of optimization criteria for LBAF execution
    """

    def __init__(self, work_model, parameters: dict=None):
        """Class constructor:
        work_model: a WorkModelBase instance
        parameters: optional parameters dictionary
        """

        # Assert that a work model base instance was passed
        if not isinstance(work_model, WorkModelBase):
            print(bcolors.ERR
                  + "*  ERROR: Could not create a criterion without a work model"
                  + bcolors.END)
            sys.exit(1)
        self.get_work = lambda x: work_model.compute(x)

        # Criterion keeps internal references to ranks and edges
        print(bcolors.HEADER
              + "[CriterionBase] "
              + bcolors.END
              + "Created base criterion with {} work model".format(
                  str(type(work_model)).split('.')[-1][:-2]
                  ))

    @staticmethod
    def factory(criterion_name, work_model, parameters={}):
        """Produce the necessary concrete criterion
        """

        from src.Execution.lbsLowerTotalWorkCriterion import LowerTotalWorkCriterion
        from src.Execution.lbsTemperedWorkCriterion import TemperedWorkCriterion
        from src.Execution.lbsStrictLocalizingCriterion import StrictLocalizingCriterion
        from src.Execution.lbsRelaxedLocalizingCriterion import RelaxedLocalizingCriterion

        # Ensure that criterion name is valid
        try:
            # Instantiate and return object
            criterion = locals()[criterion_name + "Criterion"]
            return criterion(work_model, parameters)
        except:
            # Otherwise error out
            print(bcolors.ERR
                  + "*  ERROR: Could not create a criterion with name "
                  + criterion_name
                  + bcolors.END)
            sys.exit(1)

    @abc.abstractmethod
    def compute(self, object, rank_src, rank_dst):
        """Return value of criterion for candidate object transfer
        object: Object instance
        rank_src, rank_dst: Rank instances
        """

        # Must be implemented by concrete subclass
        pass
