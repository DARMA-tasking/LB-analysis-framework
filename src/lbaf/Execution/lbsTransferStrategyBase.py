import abc
import sys
from logging import Logger

from ..Model.lbsPhase import Phase
from ..Execution.lbsCriterionBase import CriterionBase
from ..Utils.exception_handler import exc_handler
from ..Utils.logger import logger


class TransferStrategyBase:
    __metaclass__ = abc.ABCMeta
    """ An abstract base class of transfer strategies for inform and transfer algorithm."""

    def __init__(self, criterion, parameters: dict, lgr: Logger):
        """ Class constructor:
            criterion: a CriterionBase instance
            parameters: a dictionary of parameters
            lgr: a Logger instance."""

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
        lgr.info(
            f"Created base transfer strategy with {type(criterion).replace('Criterion', '')} criterion")

    @staticmethod
    def factory(
        strategy_name:str,
        parameters: dict,
        criterion: CriterionBase,
        lgr: Logger):
        """ Instantiate the necessary concrete strategy."""

        # Load up available strategies
        from .lbsRecursiveTransferStrategy import RecursiveTransferStrategy

        # Ensure that strategy name is valid
        strategy = locals()[strategy_name + "TransferStrategy"]
        return strategy(criterion, parameters, lgr)
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
    def execute(self, phase):
        """ Excecute transfer strategy on Phase instance
            phase: a Phase instance."""

        # Must be implemented by concrete subclass
        pass
