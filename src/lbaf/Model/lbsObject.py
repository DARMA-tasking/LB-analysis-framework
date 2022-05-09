from .lbsObjectCommunicator import ObjectCommunicator


class Object:
    """ A class representing an object with time and communicator
    """
    def __init__(self, i: int, t: float, p: int = None, c: ObjectCommunicator = None, user_defined: dict = None):
        # Object index
        if not isinstance(i, int) or isinstance(i, bool):
            raise TypeError(f"i: {i} is type of {type(i)}! Must be <class 'int'>!")
        else:
            self.__index = i

        # Time required to perform the work of this object
        if not isinstance(t, float):
            raise TypeError(f"t: {t} is type of {type(t)}! Must be <class 'float'>!")
        else:
            self.__time = t

        # Rank to which object is currently assigned if defined
        if bool(isinstance(p, int) or p is None) and not isinstance(p, bool):
            self.__rank_id = p
        else:
            raise TypeError(f"p: {p} is type of {type(p)}! Must be <class 'int'>!")

        # Communication graph of this object if defined
        if isinstance(c, ObjectCommunicator) or c is None:
            self.__communicator = c
        else:
            raise TypeError(f"c: {c} is type of {type(c)}! Must be <class 'ObjectCommunicator'>!")

        # User defined fields
        if isinstance(user_defined, dict) or user_defined is None:
            self.__user_defined = user_defined
        else:
            raise TypeError(f"user_defined: {user_defined} is type of {type(user_defined)}! Must be <class 'dict'>!")

    def __repr__(self):
        return f"Object id: {self.__index}, time: {self.__time}"

    def get_id(self) -> int:
        """ Return object ID
        """
        return self.__index

    def get_time(self) -> float:
        """ Return object time
        """
        return self.__time

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
