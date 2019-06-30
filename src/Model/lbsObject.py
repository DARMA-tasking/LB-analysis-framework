########################################################################
class Object:
    """A class representing an object with time and communicator
    """

    ####################################################################
    def __init__(self, i, t, s, c=None):
        # Member variables passed by constructor
        self.index           = i
        self.time            = t
        self.source          = s
        self.communicator    = c

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
    def get_source_processor(self):
        """Return processor to which object was originally attached
        """

        return self.source

    ####################################################################
    def has_communicator(self):
        """Return whether the object has communication graph data
        """

        return self.communicator != None

    ####################################################################
    def get_communicator(self):
        """Return the communication links for this object
        """

        return self.communicator

########################################################################
