#
#@HEADER
###############################################################################
#
#                              lbsWorkModelBase.py
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
from logging import Logger
import sys

from ..Utils.logger import logger


LGR = logger()


class WorkModelBase:
    __metaclass__ = abc.ABCMeta
    """ An abstract base class of per-rank work model
    """

    def __init__(self, parameters=None):
        """ Class constructor:
            parameters: optional parameters dictionary
        """
        # Work keeps internal references to ranks and edges
        LGR.debug("Created base work model")

    @staticmethod
    def factory(work_name, parameters=None, lgr: Logger = None):
        """ Produce the necessary concrete work model
        """
        from .lbsLoadOnlyWorkModel import LoadOnlyWorkModel
        from .lbsAffineCombinationWorkModel import AffineCombinationWorkModel

        # Ensure that work name is valid
        try:
            # Instantiate and return object
            work = locals()[work_name + "WorkModel"]
            return work(parameters, lgr=lgr)
        except:
            # Otherwise, error out
            LGR.error(f"Could not create a work with name {work_name}")
            sys.exit(1)

    @abc.abstractmethod
    def compute(self, rank):
        """ Return value of work for given rank
        """
        # Must be implemented by concrete subclass
        pass

    @abc.abstractmethod
    def aggregate(self, values: dict):
        """ Return value of work given relevant dictionary of values
        """
        # Must be implemented by concrete subclass
        pass
