#
#@HEADER
###############################################################################
#
#                             lbsWorkModelBase.py
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
import abc
from logging import Logger

from ..Utils.lbsLogging import get_logger


class WorkModelBase:
    """An abstract base class of per-rank work model."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, parameters=None): # pylint:disable=W0613:unused-argument # might be used in child class constructor
        """Class constructor.

        :param parameters: optional parameters dictionary.
        """
        # Work keeps internal references to ranks and edges
        get_logger().debug("Created base work model")

    @staticmethod
    def factory(work_name, parameters, lgr: Logger):
        """Produce the necessary concrete work model."""
        # pylint:disable=W0641:possibly-unused-variable,C0415:import-outside-toplevel
        from .lbsAffineCombinationWorkModel import AffineCombinationWorkModel
        from .lbsLoadOnlyWorkModel import LoadOnlyWorkModel

        # pylint:enable=W0641:possibly-unused-variable,C0415:import-outside-toplevel
        # Ensure that work name is valid
        try:
            # Instantiate and return object
            work = locals()[work_name + "WorkModel"]
            return work(parameters, lgr=lgr)
        except Exception as err:
            # Otherwise, error out
            get_logger().error(f"Could not create a work with name: {work_name}")
            raise NameError(f"Could not create a work with name: {work_name}") from err

    @abc.abstractmethod
    def compute(self, rank):
        """Return value of work for given rank."""
        # Must be implemented by concrete subclass
