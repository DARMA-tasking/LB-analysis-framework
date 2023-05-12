class Message:
    """A class representing information sent between ranks
    """

    def __init__(self, r, c):
        # Member variables passed by constructor
        self.__round = r
        self.__content = c

    def __repr__(self):
        return f"Message round: {self.__round}, Content: {self.__content}"

    def get_round(self):
        """Return message round index
        """
        return self.__round

    def get_content(self):
        """Return message content
        """
        return self.__content
