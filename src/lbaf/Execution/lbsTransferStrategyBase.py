import abc
import sys
import math
from logging import Logger

from ..Execution.lbsCriterionBase import CriterionBase
from ..Utils.exception_handler import exc_handler


class TransferStrategyBase:
    """An abstract base class of transfer strategies for inform and transfer algorithm."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, criterion, parameters: dict, lgr: Logger):
        """Class constructor.

        :param criterion: a CriterionBase instance
        :param parameters: a dictionary of parameters
        :param lgr: a Logger instance.
        """
        # Assert that a logger instance was passed
        if not isinstance(lgr, Logger):
            lgr().error(
                f"Incorrect type {type(lgr)} passed instead of Logger instance")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._logger = lgr

        # Assert that a criterion base instance was passed
        if not isinstance(criterion, CriterionBase):
            lgr.error("Could not create a transfer strategy without a criterion")
            sys.excepthook = exc_handler
            raise SystemExit(1)
        self._criterion = criterion

        # Assign optional parameters
        self._max_objects_per_transfer = parameters.get("max_objects_per_transfer", math.inf)
        self._deterministic_transfer = parameters.get("deterministic_transfer", False)
        lgr.info(
            f"Created {'' if self._deterministic_transfer else 'non'}deterministic transfer strategy, max. {self._max_objects_per_transfer} objects")

    @staticmethod
    def factory(
        strategy_name:str,
        parameters: dict,
        criterion: CriterionBase,
        lgr: Logger):
        """Instantiate the necessary concrete strategy."""
        # Load up available strategies
        # pylint:disable=C0415:import-outside-toplevel,W0641:possibly-unused-variable
        from .lbsRecursiveTransferStrategy import RecursiveTransferStrategy
        from .lbsClusteringTransferStrategy import ClusteringTransferStrategy
        # pylint:enable=C0415:import-outside-toplevel,W0641:possibly-unused-variable

        # Ensure that strategy name is valid
        try:
            # Instantiate and return object
            strategy = locals()[strategy_name + "TransferStrategy"]
            return strategy(criterion, parameters, lgr)
        except:
            # Otherwise, error out
            lgr.error(f"Could not create a strategy with name {strategy_name}")
            sys.excepthook = exc_handler
            raise SystemExit(1)

    @abc.abstractmethod
    def execute(self, phase, known_peers: dict, ave_load: float):
        """Excecute transfer strategy on Phase instance
            phase: a Phase instance
            known_peers: a dictionary of sets of known rank peers
            ave_load: average load in current phase."""

        :param phase: a Phase instance
        :param ave_load: average load in current phase.
        """
        # Must be implemented by concrete subclass
        pass
