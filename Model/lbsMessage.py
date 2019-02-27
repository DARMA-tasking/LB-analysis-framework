########################################################################
class Message:
    """A class representing load information sent by nodes
    """

    ####################################################################
    def __init__(self, r, c):
        # Member variables passed by constructor
        self.round = r
        self.content = c

    ####################################################################
    def get_round(self):
        """Return message round index
        """

        return self.round

    ####################################################################
    def get_content(self):
        """Return message content
        """

        return self.content

########################################################################
