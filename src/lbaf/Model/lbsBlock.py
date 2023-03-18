import sys

from ..Utils.exception_handler import exc_handler


class Block:
    """ A class representing a memory block with footprint and home
    """
    def __init__(
        self,
        i: int,
        h_id: int=None,
        size: float=0.0,
        comm: ObjectCommunicator=None,
        user_defined: dict=None,
        subphases: list=None):

        # Block index
        if not isinstance(i, int) or isinstance(i, bool):
            sys.excepthook = exc_handler
            raise TypeError(
                f"i: incorrect type {type(i)}")
        else:
            self.__index = i

        # Nonnegative size required to for memory footprint of this block
        if not isinstance(size, float) or size < 0.0:
            sys.excepthook = exc_handler
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        else:
            self.__size = size

        # Rank to which block is initially assigned
        if bool(isinstance(h_id, int) or h_id is None) and not isinstance(h_id, bool):
            self.__home_id = h_id
        else:
            sys.excepthook = exc_handler
            raise TypeError(
                f"h_id: incorrect type {type(h_id)}")

    def __repr__(self):
        return f"Block id: {self.__index}, size: {self.__size}"

    def get_id(self) -> int:
        """ Return block ID
        """
        return self.__index

    def get_size(self) -> float:
        """ Return block size
        """
        return self.__size

    def get_size(self) -> float:
        """ Return block size
        """
        return self.__size

    def set_home_id(self, h_id: int) -> None:
        """ Assign block to home rank ID
        """
        self.__home_id = h_id

    def get_home_id(self) -> int:
        """ Return ID of rank to which block was initially assigned
        """
        return self.__home_id
