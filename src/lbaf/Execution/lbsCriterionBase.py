import abc
from logging import Logger
from typing import List, Optional

from ..Model.lbsWorkModelBase import WorkModelBase
from ..Model.lbsPhase import Phase
from ..Utils.lbsLogging import get_logger

class CriterionBase:
    """An abstract base class of optimization criteria for LBAF execution."""

    __metaclass__ = abc.ABCMeta

    _logger: Logger

    def __init__(self, work_model: WorkModelBase, logger: Logger):
        """Class constructor:
            work_model: a WorkModelBase instance
            phase: a Phase instance
            logger: Logger instance."""

        # Assign logger to instance variable
        self._logger = logger
        logger.debug(
            f"Creating base criterion with {str(type(work_model)).rsplit('.', maxsplit=1)[-1][:-2]} work model")

        # Assert that a work model instance was passed
        if not isinstance(work_model, WorkModelBase):
            self._logger.error("Could not create a criterion without a work model")
            raise SystemExit(1)
        self._work_model = work_model

        # No phase is initially assigned
        self._phase = None

    def set_phase(self, phase: Phase):
        """Assign phase to criterion to provide access to phase methods."""

        # Assert that a phase instance was passed
        if not isinstance(phase, Phase):
            self._logger.error(f"A {type(phase)} instance was passed to set_phase()")
            raise SystemExit(1)
        self._phase = phase

    @staticmethod
    def factory(criterion_name: str, work_model: WorkModelBase, logger: Logger):
        """Produce the necessary concrete criterion."""

        # Load up available criteria
        # pylint:disable=W0641:possibly-unused-variable,C0415:import-outside-toplevel
        from .lbsTemperedCriterion import TemperedCriterion
        from .lbsStrictLocalizingCriterion import StrictLocalizingCriterion
        # pylint:enable=W0641:possibly-unused-variable,C0415:import-outside-toplevel

        # Ensure that criterion name is valid
        try:
            # Instantiate and return object
            criterion = locals()[criterion_name + "Criterion"]
            return criterion(work_model, logger)
        except Exception as e:
            # Otherwise, error out
            get_logger().error(f"Could not create a criterion with name {criterion_name}")
            raise SystemExit(1) from e

    @abc.abstractmethod
    def compute(self, r_src, o_src, r_dst, o_dst: Optional[List]=[]):
        """Compute value of criterion for candidate objects transfer

        :param r_src: iterable of objects on source
        :param o_src: Rank instance
        :param r_dst: Rank instance
        :param o_dst: optional iterable of objects on destination for swaps.
        """

        # Must be implemented by concrete subclass
        pass

    @abc.abstractmethod
    def estimate(self, r_src, o_src, r_dst_id, o_dst: Optional[List]=[]):
        """Estimate value of criterion for candidate objects transfer

        :param r_src: iterable of objects on source
        :param o_src: Rank instance
        :param r_dst_id: Rank instance ID
        :param o_dst: optional iterable of objects on destination for swaps.
        """

        # Must be implemented by concrete subclass
