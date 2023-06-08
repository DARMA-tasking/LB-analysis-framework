from logging import Logger

from .lbsWorkModelBase import WorkModelBase
from .lbsRank import Rank


class LoadOnlyWorkModel(WorkModelBase):
    """A concrete class for a load-only work model."""

    def __init__(self, _, lgr: Logger):
        """Class constructor:
            _: no parameters dictionary needed for this work model."""
        # Assign logger to instance variable
        self.__logger = lgr

        # Call superclass init
        super(LoadOnlyWorkModel, self).__init__()
        self.__logger.info("Instantiated concrete work model")

    def compute(self, rank: Rank):
        """A work model summing all object loads on given rank."""
        # Return total load on this rank
        return rank.get_load()
