import abc
from logging import Logger
import sys

from ..Utils.exception_handler import exc_handler
from ..Utils.logger import get_logger

class WorkModelBase:
    """An abstract base class of per-rank work model."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, parameters=None):
        """Class constructor.

        :param parameters: optional parameters dictionary.
        """
        # Work keeps internal references to ranks and edges
        get_logger().debug("Created base work model")

    @staticmethod
    def factory(work_name, parameters, lgr: Logger):
        """Produce the necessary concrete work model."""
        from .lbsLoadOnlyWorkModel import LoadOnlyWorkModel
        from .lbsAffineCombinationWorkModel import AffineCombinationWorkModel

        # Ensure that work name is valid
        try:
            # Instantiate and return object
            work = locals()[work_name + "WorkModel"]
            return work(parameters, lgr=lgr)
        except:
            # Otherwise, error out
            get_logger().error(f"Could not create a work with name: {work_name}")
            sys.excepthook = exc_handler
            raise NameError(f"Could not create a work with name: {work_name}")

    @abc.abstractmethod
    def compute(self, rank):
        """Return value of work for given rank."""
        # Must be implemented by concrete subclass
        pass
