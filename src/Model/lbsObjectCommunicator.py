########################################################################

from Model import lbsObject, lbsEdge

########################################################################
class ObjectCommunicator:
    """A class holding the in and out communication edges for an object
    """

    ####################################################################
    def __init__(self, i, o):
        # The set of ingoing edges
        self.in_edges = i

        # The set of outgoing edges
        self.out_edges = o

    ####################################################################
    def get_in_edges(self):
        """Return the in edges
        """

        return self.in_edges

    ####################################################################
    def get_out_edges(self):
        """Return the out edges
        """

        return self.out_edges

########################################################################
