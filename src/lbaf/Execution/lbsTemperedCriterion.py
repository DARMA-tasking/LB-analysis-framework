from logging import Logger
from typing import Optional

from .lbsCriterionBase import CriterionBase
from ..Model.lbsRank import Rank


class TemperedCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6."""

    def __init__(self, work_model, lgr: Logger):
        """Class constructor."""
        # Call superclass init
        super().__init__(work_model, lgr)
        self._logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, r_src: Rank, o_src: list, r_dst: Rank, o_dst: Optional[list]=None) -> float:
        """Tempered work criterion based on L1 norm of works."""
        if o_dst is None:
            o_dst = []

        # Compute maximum work of original arrangement
        w_max_0 = max(
            self._work_model.compute(r_src),
            self._work_model.compute(r_dst))

        # Move objects into proposed new arrangement
        self._phase.transfer_objects(r_src, o_src, r_dst, o_dst)

        # Compute maximum work of proposed new arrangement
        w_max_new = max(
            self._work_model.compute(r_src),
            self._work_model.compute(r_dst))

        # Move objects back into original arrangement
        self._phase.transfer_objects(r_dst, o_src, r_src, o_dst)

        # Return criterion value
        return w_max_0 - w_max_new
