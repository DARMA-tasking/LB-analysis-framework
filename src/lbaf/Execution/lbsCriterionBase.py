import abc
from logging import Logger
import sys

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Model.lbsPhase import Phase
from ..Utils.exception_handler import exc_handler
from ..Utils.logger import logger


class CriterionBase:
    __metaclass__ = abc.ABCMeta
    """ An abstract base class of optimization criteria for LBAF execution."""

    def __init__(self, work_model, lgr: Logger):
        """ Class constructor:
            work_model: a WorkModelBase instance
            phase: a Phase instance
            lgr: Logger instance."""

        # Assign logger to instance variable
        self._logger = lgr
        logger().debug(f"Creating base criterion with {str(type(work_model)).split('.')[-1][:-2]} work model")

        # Assert that a work model instance was passed
        if not isinstance(work_model, WorkModelBase):
            logger().error("Could not create a criterion without a work model")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._work_model = work_model

        # No phase is initially assigned
        self._phase = None

    def set_phase(self, phase: Phase):
        """ Assign phase to criterion to provide access to phase methods."""

        # Assert that a phase instance was passed
        if not isinstance(phase, Phase):
            logger().error(f"A {type(phase)} instance was passed to set_phase()")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._phase = phase

    @staticmethod
    def factory(criterion_name, work_model, lgr: Logger):
        """ Produce the necessary concrete criterion."""

        # Load up available criteria
        from .lbsTemperedCriterion import TemperedCriterion
        from .lbsStrictLocalizingCriterion import StrictLocalizingCriterion

        # Ensure that criterion name is valid
        try:
            # Instantiate and return object
            criterion = locals()[criterion_name + "Criterion"]
            return criterion(work_model, lgr)
        except:
            # Otherwise, error out
            logger().error(f"Could not create a criterion with name {criterion_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

    @abc.abstractmethod
    def compute(self, objects, rank_src, rank_dst):
        """ Return value of criterion for candidate objects transfer
            objects: iterable containing object instances
            rank_src, rank_dst: Rank instances."""

        # Must be implemented by concrete subclass
        pass
