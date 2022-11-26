from logging import Logger

from .lbsWorkModelBase import WorkModelBase
from .lbsRank import Rank


class AffineCombinationWorkModel(WorkModelBase):
    """ A concrete class for a load-only work model
    """

    def __init__(self, parameters, lgr: Logger):
        """ Class constructor:
            parameters: dictionary with alpha, beta, and gamma values
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
                f"Upper bound for {k}: {v}")
            

    def compute(self, rank: Rank):
        """ A work model with affine combination of load and communication
            alpha * load + beta * max(sent, received) + gamma
        """
        # Compute affine combination of load and volumes
        return self.__alpha * rank.get_load() + self.__beta * max(
            rank.get_received_volume(),
            rank.get_sent_volume()) + self.__gamma

    def aggregate(self, values: dict):
        """ A work model with affine combination of load and communication
            alpha * load + beta * max(sent, received) + gamma
        """
        # Return work using provided values
        return self.__alpha * values.get("load", 0.0) + self.__beta * max(
            values.get("received volume", 0.0),
            values.get("sent volume", 0.0)) + self.__gamma
