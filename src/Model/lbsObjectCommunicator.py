########################################################################
class ObjectCommunicator:
    """A class holding received and sent messages for an object
    """

    ####################################################################
    def __init__(self, r={}, s={}, i=None):
        
        # Index of object having this communicator if defined
        self.object_index = i

        # Dictionary of communications received by object
        self.received = r if isinstance(r, dict) else {}

        # Dictionary of communications sent by object
        self.sent = s if isinstance(s, dict) else {}

    ####################################################################
    def get_received(self):
        """Return all from_object=weight pairs received by object
        """

        return self.received

    ####################################################################
    def get_received_from_object(self, o):
        """Return the weight of a message received from an object if any
        """

        return self.received.get(o)

    ####################################################################
    def get_sent(self):
        """Return all to_object=weight pairs sent from object
        """

        return self.sent

    ####################################################################
    def get_sent_to_object(self, o):
        """Return the weight of a message received from an object if any
        """

        return self.sent.get(o)

    ####################################################################
    def summarize_unidirectional(self, direction, print_indent=None):
        """Summarize one-way communicator properties and check for errors
        """

        # Assert that direction is of known type
        if not direction in ("to", "from"):
            print("** ERROR: unknown direction string: {}".format(direction))
            sys.exit(1)

        # Initialize list of weights
        weights = []

        # Iterate over one-way communications
        communications = self.sent if direction == "to" else self.received
        for k, v in communications.items():
            # Sanity check
            if  k.get_id() == self.object_index:
                print("** ERROR: object {} cannot send communication to itself.".format(
                    self.object_index))
                sys.exit(1)

            # Update list of weights
            weights.append(v)

            # Report current communicaton item if requested
            if print_indent:
                print("{}{} object {}: {}".format(
                    print_indent,
                    "->" if direction == "to" else "<-",
                    k.get_id(),
                    v))

        # Return list of weights
        return weights

    ####################################################################
    def summarize(self, print_indent=None):
        """Summarize communicator properties and check for errors
        """

        # Summarize sent communications
        w_sent = self.summarize_unidirectional("to", print_indent)

        # Summarize received communications
        w_recv = self.summarize_unidirectional("from", print_indent)

        # Return counters
        return w_sent, w_recv

########################################################################
