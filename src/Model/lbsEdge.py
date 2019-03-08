########################################################################

from Model import Object;

########################################################################
class Edge:
    """A class representing the communication edge between two nodes (Object)
    in the communication graph

    """

    ####################################################################
    def __init__(self, obj_send, obj_recv, weight):
        # The Object that sends data along this edge
        self.obj_send  = obj_send

        # The Object that receives data along this edge
        self.obj_recv = obj_recv

        # The weight of the edge in bytes
        self.weight  = weight

    ####################################################################
    def get_send_obj(self):
        """Return the Object that sent along this edge
        """

        return self.obj_send

    ####################################################################
    def get_recv_obj(self):
        """Return the Object that received along this edge
        """

        return self.obj_recv

    ####################################################################
    def get_weight(self):
        """Return the weight of the edge (number of bytes)
        """

        return self.weight

########################################################################
