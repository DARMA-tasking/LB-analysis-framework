from logging import Logger

from .lbsCriterionBase import CriterionBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsRank import Rank


class TemperedCriterion(CriterionBase):
    """ A concrete class for the Grapevine criterion modified in line 6."""

    def __init__(self, work_model, lgr):
        """ Class constructor."""

        # Call superclass init
        super().__init__(work_model, lgr)
        self._logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, objects: list, r_src: Rank, r_dst: Rank) -> float:
        """ Tempered work criterion based on L1 norm of works."""

        # Compute maximum work of original arrangement
        w_max_0 = max(
            self._work_model.compute(r_src),
            self._work_model.compute(r_dst))

        # Move objects into proposed new arrangement
        for o in objects:
            self._phase.transfer_object(o, r_src, r_dst)

        # Compute maximum work of proposed new arrangement
        w_max_new = max(
            self._work_model.compute(r_src),
            self._work_model.compute(r_dst))

        # Move objects back into original arrangement
        for o in objects:
            self._phase.transfer_object(o, r_dst, r_src)

        # Return criterion value
        return w_max_0 - w_max_new




