import abc
import sys
import math
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
        """ Instantiate the necessary concrete strategy."""

        # Load up available strategies
        from .lbsRecursiveTransferStrategy import RecursiveTransferStrategy
        from .lbsClusteringTransferStrategy import ClusteringTransferStrategy

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
    def execute(self, phase, ave_load):
        """ Excecute transfer strategy on Phase instance
            phase: a Phase instance
            ave_load: average load in current phase."""

        # Must be implemented by concrete subclass
        pass

    def _transfer_objects(self, phase, objects, r_src, r_dst):
        """ Perform sanity check and transfer list of objects."""

        # Sanity check before transfer
        if r_dst not in r_src.get_known_loads():
            self._logger.error(
                f"Destination rank {r_dst.get_id()} not in known ranks")
            sys.excepthook = exc_handler
            raise SystemExit(1)

        # Transfer objects and return number of transferred objects
        for o in objects:
            phase.transfer_object(o, r_src, r_dst)
        n_transfers = len(objects)

        # Report and return number of transferred objects
        self._logger.info(
            f"Transferred {n_transfers} objects from rank {r_src.get_id()} to {r_dst.get_id()}")
        return n_transfers

    def _swap_objects(self, phase, o_src, r_src, o_dst, r_dst):
        """ Swap list of objects between two ranks."""

        # Ensure source rank is known to destination
        r_dst.add_known_load(r_src)

        # Transfer objects between ranks
        n_transfers = self._transfer_objects(phase, o_src, r_src, r_dst)
        n_transfers += self._transfer_objects(phase, o_dst, r_dst, r_src)

        # Return number of transferred objects
        return n_transfers
