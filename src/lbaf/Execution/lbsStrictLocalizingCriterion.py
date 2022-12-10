from logging import Logger

from .lbsCriterionBase import CriterionBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsRank import Rank


class StrictLocalizingCriterion(CriterionBase):
    """ A concrete class for a strictly localizing criterion
    """
    
    def __init__(self, workmodel, lgr):
        """ Class constructor."""

        # Call superclass init
        super().__init__(workmodel, lgr)
        self._logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, object: list, p_src: Rank, _):
        """ A criterion enforcing strict conservation of local communications."""

        # Keep track source processor ID
        p_src_id = p_src.get_id()

        # Retrieve object communications
        # TODO: compute method should be updated like `TemperedCriterion`, object is a list, so iteration is needed
        comm = object.get_communicator()

        # Iterate over sent messages
        if not isinstance(comm, ObjectCommunicator):
            self.__logger.warning(f"Object {object.get_id()} has no communicator")
            return 0.

        # Iterate over sent messages
        for i in comm.get_sent().items():
            if p_src_id == i[0].get_rank_id():
                # Bail out as soon as locality is broken by transfer
                return -1.

        # Iterate over received messages
        for i in comm.get_received().items():
            if p_src_id == i[0].get_rank_id():
                # Bail out as soon as locality is broken by transfer
                return -1.

        # Criterion returns a positive value meaning acceptance
        return 1.
