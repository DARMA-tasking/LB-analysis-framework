from typing import List

from .lbsCriterionBase import CriterionBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsObject import Object
from ..Model.lbsRank import Rank


class StrictLocalizingCriterion(CriterionBase):
    """A concrete class for a strictly localizing criterion."""

    def __init__(self, workmodel, lgr):
        """Class constructor."""
        # Call superclass init
        super().__init__(workmodel, lgr)
        self._logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, r_src: Rank, o_src: List[Object], *_args) -> float:
        """A criterion enforcing strict conservation of local communications."""
        # Keep track source processor ID
        r_src_id = r_src.get_id()

        # Iterate over objects proposed for transfer
        for o in o_src:
            # Retrieve object communications
            comm = o.get_communicator()

            # Ignore object if it does not have a communicator
            if not isinstance(comm, ObjectCommunicator):
                continue

            # Iterate over sent messages
            for i in comm.get_sent().items():
                if r_src_id == i[0].get_rank_id():
                    # Bail out as soon as locality is broken by transfer
                    return -1.

            # Iterate over received messages
            for i in comm.get_received().items():
                if r_src_id == i[0].get_rank_id():
                    # Bail out as soon as locality is broken by transfer
                    return -1.

        # Accept transfer if this point was reached as no locality was broken
        return 1.

    def estimate(self, r_src: Rank, o_src: list, *args) -> float:
        """Estimate is compute because all information is local for this criterion."""
        return self.compute(r_src, o_src, *args)
