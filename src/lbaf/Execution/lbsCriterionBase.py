import abc
from logging import Logger
import sys

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Utils.logger import logger


LGR = logger()


class CriterionBase:
    __metaclass__ = abc.ABCMeta
    """ An abstract base class of optimization criteria for LBAF execution
    """

    def __init__(self, work_model):
        """ Class constructor:
            work_model: a WorkModelBase instance
        """

        # Assert that a work model base instance was passed
        if not isinstance(work_model, WorkModelBase):
            LGR.error("Could not create a criterion without a work model")
            raise SystemExit(1)
        self.work_model = work_model

        # Criterion keeps internal references to ranks and edges
        LGR.debug(f"Created base criterion with {str(type(work_model)).split('.')[-1][:-2]} work model")

    @staticmethod
    def factory(criterion_name, work_model, lgr: Logger):
        """ Produce the necessary concrete criterion
        """

        # Load up available criteria
        from .lbsTemperedCriterion import TemperedCriterion
        from .lbsStrictLocalizingCriterion import StrictLocalizingCriterion

        # Ensure that criterion name is valid
        try:
            # Instantiate and return object
            criterion = locals()[criterion_name + "Criterion"]
            return criterion(work_model, lgr=lgr)
        except:
            # Otherwise, error out
            LGR.error(f"Could not create a criterion with name {criterion_name}")
            raise SystemExit(1)

    @abc.abstractmethod
    def compute(self, objects, rank_src, rank_dst):
        """ Return value of criterion for candidate objects transfer
            objects: iterable containing object instances
            rank_src, rank_dst: Rank instances
        """

        # Must be implemented by concrete subclass
        pass
