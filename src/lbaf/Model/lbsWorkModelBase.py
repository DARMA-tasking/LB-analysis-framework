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
    def factory(work_name, parameters, lgr: Logger):
        """ Produce the necessary concrete work model
        """
        from .lbsLoadOnlyWorkModel import LoadOnlyWorkModel
        from .lbsAffineCombinationWorkModel import AffineCombinationWorkModel

        # Ensure that work name is valid
        # TODO: not needed anymore, because of configuration schema cheking
        try:
            # Instantiate and return object
            work = locals()[work_name + "WorkModel"]
            return work(parameters, lgr=lgr)
        except:
            # Otherwise, error out
            LGR.error(f"Could not create a work with name: {work_name}")
            raise NameError(f"Could not create a work with name: {work_name}")

    @abc.abstractmethod
    def compute(self, rank):
        """ Return value of work for given rank
        """
        # Must be implemented by concrete subclass

    @abc.abstractmethod
    def aggregate(self, values: dict):
        """ Return value of work given relevant dictionary of values
        """
        # Must be implemented by concrete subclass
