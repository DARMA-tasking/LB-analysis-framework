import abc
from logging import Logger
from typing import List, Optional
import sys

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Model.lbsPhase import Phase
from ..Utils.exception_handler import exc_handler
from ..Utils.logger import logger


class CriterionBase:
    """An abstract base class of optimization criteria for LBAF execution."""

    __metaclass__ = abc.ABCMeta
    _logger: Logger

    def __init__(self, work_model: WorkModelBase, lgr: Logger):
        """Class constructor:
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
        """Assign phase to criterion to provide access to phase methods."""

        # Assert that a phase instance was passed
        if not isinstance(phase, Phase):
            logger().error(f"A {type(phase)} instance was passed to set_phase()")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._phase = phase

    @staticmethod
    def factory(criterion_name: str, work_model: WorkModelBase, lgr: Logger):
        """Produce the necessary concrete criterion."""

        # Load up available criteria
        # pylint:disable=W0641,C0415
        from .lbsTemperedCriterion import TemperedCriterion
        from .lbsStrictLocalizingCriterion import StrictLocalizingCriterion
        # pylint:enable=W0641,C0415

        # Ensure that criterion name is valid
        try:
            # Instantiate and return object
            criterion = locals()[criterion_name + "Criterion"]
            return criterion(work_model, lgr)
        except Exception as ex:
            # Otherwise, error out
            logger().error(f"Could not create a criterion with name {criterion_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1) from ex

    @abc.abstractmethod
    def compute(self, r_src, o_src, r_dst, o_dst: Optional[List]=None):
        """Return value of criterion for candidate objects transfer

        :param r_src: iterable of objects on source
        :param o_src: Rank instance
        :param r_dst: Rank instance
        :param o_dst: optional iterable of objects on destination for swaps.
        """

        if o_dst is None:
            o_dst = []

        # Must be implemented by concrete subclass
        pass # pylint:disable=W0107
