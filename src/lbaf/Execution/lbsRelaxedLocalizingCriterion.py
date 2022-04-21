import functools
from logging import Logger

from .lbsCriterionBase import CriterionBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator


class RelaxedLocalizingCriterion(CriterionBase):
    """A concrete class for a relaxedly localizing criterion
    """

    def __init__(self, ranks, edges, _, lgr: Logger = None):
        """ Class constructor:
            ranks: set of ranks (lbsRank.Rank instances)
            edges: dictionary of edges (pairs)
            _: no parameters dictionary needed for this criterion
        """

        # Call superclass init
        super(RelaxedLocalizingCriterion, self).__init__(ranks, edges)

        # Assign logger to instance variable
        self.__logger = lgr
        self.__logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, object, p_src, p_dst):
        """A criterion allowing for local disruptions for more locality
        """

        # Retrieve object communications
        comm = object.get_communicator()
        if not isinstance(comm, ObjectCommunicator):
            self.__logger.warning(f"Object {object.get_id()} has no communicator")
            return 0.

        # Retrieve sent and received items from communicator
        sent = comm.get_sent().items()
        recv = comm.get_received().items()

        # Retrieve ID of rank to which an object is assigned
        p_id = (lambda x: x.get_rank_id())

        # Test whether first component is source rank
        is_s = (lambda x: p_id(x[0]) == p_src.get_id())

        # Test whether first component is destination rank
        is_d = (lambda x: p_id(x[0]) == p_dst.get_id())

        # Add value with second components of a collection
        xPy1 = (lambda x, y: x + y[1])

        # Aggregate communication volumes with source
        w_src = functools.reduce(xPy1, list(filter(is_s, recv)) + list(filter(is_s, sent)), 0.)

        # Aggregate communication volumes with destination
        w_dst = functools.reduce(xPy1, list(filter(is_d, recv)) + list(filter(is_d, sent)), 0.)

        # Criterion assesses difference in local communications
        return w_dst - w_src
