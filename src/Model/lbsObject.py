
########################################################################
class Object:
    """A class representing an instance of a class and its communication
    """

    ####################################################################
    def __init__(self, i, t, p=0, c=None):
        # Member variables passed by constructor
        self.index = i
        self.time  = t
        self.comm  = c
        self.phase = p

    ####################################################################
    def get_id(self):
        """Return object ID
        """

        return self.index

    ####################################################################
    def get_time(self):
        """Return object time
        """

        return self.time

    ####################################################################
    def get_phase(self):
        """Return object phase/iteration
        """

        return self.phase
    ####################################################################
    def has_comm(self):
        """Return whether the object has communication graph data
        """

        return self.comm != None

    ####################################################################
    def get_comm(self):
        """Return the comm links for this Object
        """

        return self.comm

########################################################################
