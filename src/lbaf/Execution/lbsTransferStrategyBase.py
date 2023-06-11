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


    def _compute_transfer_cmf(self, r_src, objects: list, targets: set, strict=False):
        """Compute CMF for the sampling of transfer targets."""
        # Initialize criterion values
        c_values = {}
        c_min, c_max = math.inf, -math.inf

        # Iterate over potential targets
        for r_dst in targets:
            # Compute value of criterion for current target
            c_dst = self._criterion.compute(r_src, objects, r_dst)

            # Do not include rejected targets for strict CMF
            if strict and c_dst < 0.:
                continue

            # Update criterion values
            c_values[r_dst] = c_dst
            if c_dst < c_min:
                c_min = c_dst
            if c_dst > c_max:
                c_max = c_dst

        # Initialize CMF depending on singleton or non-singleton support
        if c_min == c_max:
            # Sample uniformly if all criteria have same value
            cmf = {k: 1.0 / len(c_values) for k in c_values.keys()}
        else:
            # Otherwise, use relative weights
            c_range = c_max - c_min
            cmf = {k: (v - c_min) / c_range for k, v in c_values.items()}

        # Compute CMF
        sum_p = 0.0
        for k, v in cmf.items():
            sum_p += v
            cmf[k] = sum_p

        # Return normalized CMF and criterion values
        return {k: v / sum_p for k, v in cmf.items()}, c_values

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
        """Execute transfer strategy on Phase instance
        :param phase: a Phase instance
        :param known_peers: a dictionary of sets of known rank peers
        :param ave_load: average load in current phase.
        """
        # Must be implemented by concrete subclass
        pass
