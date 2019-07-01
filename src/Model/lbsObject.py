########################################################################

from Model import lbsObjectCommunicator

########################################################################
class Object:
    """A class representing an object with time and communicator
    """

    ####################################################################
    def __init__(self, i, t, s=None, c=None):
        # Object index
        self.index = i

        # Time required to perform the work of this object
        self.time = t

        # Processor to which object was originally attached
        self.source = s

        # Communication graph of this object
        self.communicator = c if isinstance(
            c, lbsObjectCommunicator.ObjectCommunicator) else None

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
        """Return the communication graph for this object
        """

        return self.communicator

    ####################################################################
    def set_communicator(self, c):
        """Assign the communication graph for this object
        """

        # Perform sanity check prior to assignment
        if isinstance(c, lbsObjectCommunicator.ObjectCommunicator):
            self.communicator = c

########################################################################
