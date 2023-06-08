import math
from logging import Logger

from .lbsWorkModelBase import WorkModelBase
from .lbsRank import Rank


class AffineCombinationWorkModel(WorkModelBase):
    """A concrete class for a load-only work model"""

    def __init__(self, parameters, lgr: Logger):
        """Class constructor:

        parameters: dictionary with alpha, beta, and gamma values.
        """
        # Assign logger to instance variable
        self.__logger = lgr

        # Use default values if parameters not provided
        self.__alpha = parameters.get("alpha", 1.0)
        self.__beta = parameters.get("beta", 0.0)
        self.__gamma = parameters.get("gamma", 0.0)
        self.__upper_bounds = parameters.get("upper_bounds", {})

        # Call superclass init
        super(AffineCombinationWorkModel, self).__init__(parameters)
        self.__logger.info(
            f"Instantiated work model with alpha={self.__alpha}, beta={self.__beta}, gamma={self.__gamma}")
        for k, v in self.__upper_bounds.items():
            self.__logger.info(
                f"Upper bound for rank {k}: {v}")

    def get_alpha(self):
        """Get the alpha parameter."""
        return self.__alpha

    def get_beta(self):
        """Get the beta parameter."""
        return self.__beta

    def get_gamma(self):
        """Get the gamma parameter."""
        return self.__gamma

    def affine_combination(self, l, v1, v2):
        """Compute affine combination of load and maximum volume."""
        return self.__alpha * l + self.__beta * max(v1, v2) + self.__gamma

    def compute(self, rank: Rank):
        """A work model with affine combination of load and communication.

        alpha * load + beta * max(sent, received) + gamma,
        under optional strict upper bounds.
        """
        # Check whether strict bounds are satisfied
        for k, v in self.__upper_bounds.items():
            if getattr(rank, f"get_{k}")() > v:
                return math.inf

        # Return combination of load and volumes
        return self.affine_combination(
            rank.get_load(),
            rank.get_received_volume(),
            rank.get_sent_volume())
