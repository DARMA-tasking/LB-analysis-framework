from logging import Logger


class ObjectCommunicator:
    """A class holding received and sent messages for an object."""

    def __init__(self, i: int, logger: Logger, r: dict = None, s: dict = None):
        """Class constructor."""
        # Index of object having this communicator if defined
        self.__object_index = i

        # Dictionary of communications received by object
        self.__received = r if isinstance(r, dict) else {}

        # Dictionary of communications sent by object
        self.__sent = s if isinstance(s, dict) else {}

        # Assign logger to instance variable
        self.__logger = logger

    def __summarize_unidirectional(self, direction):
        """Summarize one-way communicator properties and check for errors."""
        # Initialize list of volumes
        volumes = []

        # Iterate over one-way communications
        communications = self.__sent if direction == "to" else self.__received
        for k, v in communications.items():
            # Sanity check
            if k.get_id() == self.__object_index:
                self.__logger.error(f"object {self.__object_index} cannot send communication to itself.")
                raise IndexError(f"object {self.__object_index} cannot send communication to itself.")

            # Update list of volumes
            volumes.append(v)

            # Report current communication item if requested
            self.__logger.debug(f'{"->" if direction == "to" else "<-"} object {k.get_id()}: {v}')

        # Return list of volumes
        return volumes

    def get_received(self) -> dict:
        """Return all from_object=volume pairs received by object."""
        return self.__received

    def get_received_from_object(self, o):
        """Return the volume of a message received from an object if any."""
        return self.__received.get(o)

    def get_sent(self) -> dict:
        """Return all to_object=volume pairs sent from object."""
        return self.__sent

    def get_sent_to_object(self, o):
        """Return the volume of a message received from an object if any."""
        return self.__sent.get(o)

    def summarize(self) -> tuple:
        """Summarize communicator properties and check for errors."""
        # Summarize sent communications
        w_sent = self.__summarize_unidirectional("to")

        # Summarize received communications
        w_recv = self.__summarize_unidirectional("from")

        # Return counters
        return w_sent, w_recv
