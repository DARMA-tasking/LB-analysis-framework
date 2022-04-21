import abc
from logging import Logger
import sys

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Utils.logger import logger


LGR = logger()


class AlgorithmBase:
    __metaclass__ = abc.ABCMeta
    """ An abstract base class of load/work balancing algorithms
    """

    def __init__(self, work_model, parameters: dict = None):
        """ Class constructor:
            work_model: a WorkModelBase instance
            parameters: optional parameters dictionary
        """

        # Assert that a work model base instance was passed
        if not isinstance(work_model, WorkModelBase):
            LGR.error("Could not create an algorithm without a work model")
            sys.exit(1)
        self.work_model = work_model

        # Algorithm keeps internal references to ranks and edges
        LGR.debug(f"Created base balancing algorithm")

    @staticmethod
    def factory(algorithm_name:str, work_model, parameters={}, lgr: Logger = None):
        """ Produce the necessary concrete algorithm
        """

        # Load up available algorithms
        from .lbsInformAndTransferAlgorithm import InformAndTransferAlgorithm

        algorithm = locals()[algorithm_name + "Algorithm"]
        return algorithm(work_model, parameters, lgr=lgr)
        # Ensure that algorithm name is valid
        try:
            # Instantiate and return object
            algorithm = locals()[algorithm_name + "Algorithm"]
            return algorithm(work_model, parameters, lgr=lgr)
        except:
            # Otherwise, error out
            LGR.error(f"Could not create an algorithm with name {algorithm_name}")
            sys.exit(1)

    @abc.abstractmethod
    def execute(self, phase):
        """ Excecute algorithm on given phase
            phase: Phase instance
        """

        # Must be implemented by concrete subclass
        pass
