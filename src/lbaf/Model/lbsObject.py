import sys

from .lbsObjectCommunicator import ObjectCommunicator
from ..Utils.exception_handler import exc_handler


class Object:
    """ A class representing an object with load and communicator
    """
    def __init__(
        self, i: int, t: float, p: int = None, c: ObjectCommunicator = None, user_defined: dict = None, subphases: list = None):
        # Object index
        if not isinstance(i, int) or isinstance(i, bool):
            sys.excepthook = exc_handler
            raise TypeError(f"i: {i} is of type {type(i)} but must be <class 'int'>")
        else:
            self.__index = i

        # Load required to perform the work of this object
        if not isinstance(t, float):
            sys.excepthook = exc_handler
            raise TypeError(f"t: {t} is of type {type(t)} but must be <class 'float'>")
        else:
            self.__load = t

        # Rank to which object is currently assigned if defined
        if bool(isinstance(p, int) or p is None) and not isinstance(p, bool):
            self.__rank_id = p
        else:
            sys.excepthook = exc_handler
            raise TypeError(f"p: {p} is of type {type(p)} Must be <class 'int'>")

        # Communication graph of this object if defined
        if isinstance(c, ObjectCommunicator) or c is None:
            self.__communicator = c
        else:
            sys.excepthook = exc_handler
            raise TypeError(f"c: {c} is of type {type(c)} Must be <class 'ObjectCommunicator'>")

        # User defined fields
        if isinstance(user_defined, dict) or user_defined is None:
            self.__user_defined = user_defined
        else:
            sys.excepthook = exc_handler
            raise TypeError(f"user_defined: {user_defined} is of type {type(user_defined)} but must be <class 'dict'>")

        # Sub-phases
        if isinstance(subphases, list) or subphases is None:
            self.__subphases = subphases
        else:
            sys.excepthook = exc_handler
            raise TypeError(f"subphases: {subphases} is of type {type(subphases)} but must be <class 'list'>")

    def __repr__(self):
        return f"Object id: {self.__index}, load: {self.__load}"

    def get_id(self) -> int:
        """ Return object ID
        """
        return self.__index

    def get_load(self) -> float:
        """ Return object load
        """
        return self.__load

    def get_sent(self) -> dict:
        """ Return communications sent by object to other objects
        """
        return self.__communicator.get_sent() if self.__communicator else {}

    def get_received(self) -> dict:
        """ Return communications received by object from other objects
        """
        return self.__communicator.get_received() if self.__communicator else {}

    def get_received_volume(self) -> float:
        """ Return volume of communications received by object
        """
        return sum([v for v in self.__communicator.get_received().values()]) if self.__communicator else 0

    def get_sent_volume(self) -> float:
        """ Return volume of communications sent by object
        """
        return sum([v for v in self.__communicator.get_sent().values()]) if self.__communicator else 0

    def set_rank_id(self, p_id) -> None:
        """ Assign object to rank ID
        """
        self.__rank_id = p_id

    def get_rank_id(self) -> int:
        """ Return ID of rank to which object is currently assigned
        """
        return self.__rank_id

    def has_communicator(self) -> bool:
        """ Return whether the object has communication graph data
        """
        return self.__communicator is not None

    def get_communicator(self) -> ObjectCommunicator:
        """ Return the communication graph for this object
        """
        return self.__communicator

    def set_communicator(self, c) -> None:
        """ Assign the communication graph for this object
        """
        # Perform sanity check prior to assignment
        if isinstance(c, ObjectCommunicator):
            self.__communicator = c

    def get_subphases(self) -> list:
        """ Return subphases of this object
        """
        return self.__subphases
