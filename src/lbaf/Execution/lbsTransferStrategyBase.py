import abc
import math
from logging import Logger

from ..Execution.lbsCriterionBase import CriterionBase
from ..Utils.lbsException import TerseError

class TransferStrategyBase:
    """An abstract base class of transfer strategies for inform and transfer algorithm."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, criterion, parameters: dict, logger: Logger):
        """Class constructor.

        :param criterion: a CriterionBase instance
        :param parameters: a dictionary of parameters
        :param logger: a Logger instance.
        """
        # Assert that a logger instance was passed
        if not isinstance(logger, Logger):
            raise TerseError(f"Incorrect type {type(logger)} passed instead of Logger instance")
        self._logger = logger

        # Assert that a criterion base instance was passed
        if not isinstance(criterion, CriterionBase):
            raise TerseError("Could not create a transfer strategy without a criterion")
        self._criterion = criterion

        # Assign optional parameters
        self._max_objects_per_transfer = parameters.get("max_objects_per_transfer", math.inf)
        self._deterministic_transfer = parameters.get("deterministic_transfer", False)
        logger.info(
            f"Created {'' if self._deterministic_transfer else 'non'}deterministic transfer strategy, max. {self._max_objects_per_transfer} objects")

    @staticmethod
    def factory(
        strategy_name:str,
        parameters: dict,
        criterion: CriterionBase,
        logger: Logger):
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
            return strategy(criterion, parameters, logger)
        except Exception as error:
            # Otherwise, error out
            raise TerseError(f"Could not create a strategy with name {strategy_name}") from error

    @abc.abstractmethod
    def execute(self, phase, ave_load):
        """Excecute transfer strategy on Phase instance

        :param phase: a Phase instance
        :param ave_load: average load in current phase.
        """
        # Must be implemented by concrete subclass
