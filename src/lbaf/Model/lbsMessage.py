class Message:
    """A class representing information sent between ranks."""

    def __init__(self, r: int, s: set):
        # Member variables passed by constructor
        self.__round = r
        self.__support = s

    def __repr__(self):
        return f"Message at round: {self.__round}, support: {self.__support}"

    def get_round(self):
        """Return message round index."""
        return self.__round

    def get_support(self):
        """Return message support."""
        return self.__support
