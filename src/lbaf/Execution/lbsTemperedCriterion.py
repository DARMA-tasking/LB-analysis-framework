from logging import Logger

from .lbsCriterionBase import CriterionBase
from ..Model.lbsObjectCommunicator import ObjectCommunicator
from ..Model.lbsRank import Rank


class TemperedCriterion(CriterionBase):
    """ A concrete class for the Grapevine criterion modified in line 6
    """

    def __init__(self, work_model, lgr: Logger):
        """ Class constructor
            work_model: WorkModelBase instance
        """

        # Call superclass init
        super().__init__(work_model)

        # Assign logger to instance variable
        self.__logger = lgr
        self.__logger.info(f"Instantiated {type(self).__name__} concrete criterion")

    def compute(self, objects: list, p_src: Rank, p_dst: Rank) -> float:
        """ Tempered work criterion based on L1 norm of works
        """
        # Compute original arrangement works
        values_src = {
            "load": p_src.get_load(),
            "received volume": p_src.get_received_volume(),
            "sent volume": p_src.get_sent_volume()}
        w_src_0 = self.work_model.aggregate(values_src)
        values_dst = {
            "load": p_dst.get_load(),
            "received volume": p_dst.get_received_volume(),
            "sent volume": p_dst.get_sent_volume()}
        w_dst_0 = self.work_model.aggregate(values_dst)
        w_max_0 = max(w_src_0, w_dst_0)

        # Update loads in proposed new arrangement
        object_loads = sum([o.get_load() for o in objects])
        values_src["load"] -= object_loads
        values_dst["load"] += object_loads

        # Retrieve IDs of source and destination ranks
        src_id = p_src.get_id()
        dst_id = p_dst.get_id()

        # Update communication volumes
        v_src_to_src = 0.
        v_src_to_dst = 0.
        v_src_to_oth = 0.
        v_src_from_src = 0.
        v_src_from_dst = 0.
        v_src_from_oth = 0.
        for o in objects:
            # Skip objects without a communicator
            comm = o.get_communicator()
            if not isinstance(comm, ObjectCommunicator):
                continue

            # Retrieve items not sent nor received from object list
            recv = {(k, v) for k, v in comm.get_received().items()
                    if k not in objects}
            sent = {(k, v) for k, v in comm.get_sent().items()
                    if k not in objects}

            # Tally sent communication volumes by destination
            for k, v in sent:
                if k.get_rank_id() == src_id:
                    v_src_to_src += v
                elif k.get_rank_id() == dst_id:
                    v_src_to_dst += v
                else:
                    v_src_to_oth += v

            # Tally received communication volumes by source
            for k, v in recv:
                if k.get_rank_id() == src_id:
                    v_src_from_src += v
                elif k.get_rank_id() == dst_id:
                    v_src_from_dst += v
                else:
                    v_src_from_oth += v

        # Update volumes by transferring non-local communications
        values_src["sent volume"] -= v_src_to_dst + v_src_to_oth
        values_dst["sent volume"] += v_src_to_src + v_src_to_oth
        values_src["received volume"] -= v_src_from_dst + v_src_from_oth
        values_dst["received volume"] += v_src_from_src + v_src_from_oth

        # Swap sent/recieved volumes for local commmunications
        values_src["sent volume"] += v_src_from_src
        values_dst["sent volume"] -= v_src_from_dst 
        values_src["received volume"] += v_src_to_src
        values_dst["received volume"] -= v_src_to_dst

        # Compute proposed new arrangement works
        w_src_new = self.work_model.aggregate(values_src)
        w_dst_new = self.work_model.aggregate(values_dst)
        w_max_new = max(w_src_new, w_dst_new)

        # Return criterion value
        return w_max_0 - w_max_new
