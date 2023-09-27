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
