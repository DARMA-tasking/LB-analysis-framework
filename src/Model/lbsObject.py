
########################################################################
class Object:
    """A class representing an instance of a class and its communication
    """

    ####################################################################
    def __init__(self, i, t, s, c=None):
        # Member variables passed by constructor
        self.index           = i
        self.time            = t
        self.source          = s
        self.communications  = c

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
    def has_communications(self):
        """Return whether the object has communication graph data
        """

        return self.communications != None

    ####################################################################
    def get_communications(self):
        """Return the comm links for this Object
        """

        return self.communications

########################################################################
