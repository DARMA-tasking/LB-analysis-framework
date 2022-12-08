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

        # Compute loads in proposed new arrangement
        object_loads = sum([o.get_load() for o in objects])
        values_src = {
            "load": r_src.get_load() - object_loads}
        values_dst = {
            "load": r_dst.get_load() + object_loads}

        # Retrieve IDs of source and destination ranks
        src_id = r_src.get_id()
        dst_id = r_dst.get_id()

        # Initialize volume changes for proposed new arrangements
        v_src_to_src = 0.
        v_src_to_dst = 0.
        v_src_to_oth = 0.
        v_src_from_src = 0.
        v_src_from_dst = 0.
        v_src_from_oth = 0.

        # Iterate over objects to be transferred
        for o in objects:
            # Skip objects without a communicator
            comm = o.get_communicator()
            if not isinstance(comm, ObjectCommunicator):
                continue

            # Tally sent communication volumes by destination
            for k, v in comm.get_sent().items():
                # Skip items sent to object list
                if k in objects:
                    continue

                # Categorize sent volume
                if k.get_rank_id() == src_id:
                    v_src_to_src += v
                elif k.get_rank_id() == dst_id:
                    v_src_to_dst += v
                else:
                    v_src_to_oth += v

            # Tally received communication volumes by source
            for k, v in comm.get_received().items():
                # Skip items received from object list
                if k in objects:
                    continue

                # Categorize received volume
                if k.get_rank_id() == src_id:
                    v_src_from_src += v
                elif k.get_rank_id() == dst_id:
                    v_src_from_dst += v
                else:
                    v_src_from_oth += v

        # Initialize volumes with pre-transfer communications
        values_src["sent volume"] = r_src.get_sent_volume()
        values_dst["sent volume"] = r_dst.get_sent_volume()
        values_src["received volume"] = r_src.get_received_volume()
        values_dst["received volume"] = r_dst.get_received_volume()

        # Update volumes by transferring non-local communications
        values_src["sent volume"] -= v_src_to_dst + v_src_to_oth
        values_dst["sent volume"] += v_src_to_src + v_src_to_oth
        values_src["received volume"] -= v_src_from_dst + v_src_from_oth
        values_dst["received volume"] += v_src_from_src + v_src_from_oth

        # Swap sent/received volumes for local commmunications
        values_src["sent volume"] += v_src_from_src
        values_dst["sent volume"] -= v_src_from_dst 
        values_src["received volume"] += v_src_to_src
        values_dst["received volume"] -= v_src_to_dst

        # Compute proposed new arrangement works
        w_max_new = max(
            self._work_model.aggregate(values_src),
            self._work_model.aggregate(values_dst))
