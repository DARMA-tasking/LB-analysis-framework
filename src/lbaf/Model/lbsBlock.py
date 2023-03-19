import sys

from ..Utils.exception_handler import exc_handler


class Block:
    """ A class representing a memory block with footprint and home
    """
    def __init__(
        self,
        i: int,
        h_id: int,
        size: float=0.0,
        o_ids: set=set()):

        # Block index
        if not isinstance(i, int) or isinstance(i, bool):
            sys.excepthook = exc_handler
            raise TypeError(
                f"i: incorrect type {type(i)}")
        else:
            self.__index = i

        # Rank to which block is initially assigned
        if not isinstance(h_id, int) or isinstance(i, bool):
            sys.excepthook = exc_handler
            raise TypeError(
                f"h_id: incorrect type {type(h_id)}")
        self.__home_id = h_id

        # Nonnegative size required to for memory footprint of this block
        if not isinstance(size, float) or size < 0.0:
            sys.excepthook = exc_handler
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        self.__size = size

        # Possibly empty set of objects initially attached to block
        if not isinstance(o_ids, set):
            sys.excepthook = exc_handler
            raise TypeError(
                f"o_ids: incorrect type {type(o_ids)}")
        self.__attached_object_ids = o_ids

    def __repr__(self):
        return f"Block id: {self.__index}, home id: {self.__home_id}, size: {self.__size}, object ids: {self.__attached_object_ids}"

    def get_id(self) -> int:
        """ Return block ID
        """
        return self.__index

    def get_home_id(self) -> int:
        """ Return block home ID
        """
        return self.__home_id

    def get_size(self) -> float:
        """ Return block size
        """
        return self.__size

    def detach_object_id(self, o_id: int) -> int:
        """ Try to detach object ID from block and return length
        """
        try:
            self.__attached_object_ids.remove(o_id)
        except:
            raise TypeError(
                f"object id {o_id} is not attached to block {self.get_id()}")
        return len(self.__attached_object_ids)

    def attach_object_id(self, o_id: int):
        """ Attach object ID to block
        """
        self.__attached_object_ids.add(o_id)
