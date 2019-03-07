########################################################################

from Model import Object, Edge;

########################################################################
class ObjComm:
    """A class that holds the in and out edges for an object

    """

    ####################################################################
    def __init__(self, in_edges, out_edges):
        # The set of in edges for a given object
        self.in_edges = in_edges

        # The set of out edges for a given object
        self.out_edges = out_edges

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
