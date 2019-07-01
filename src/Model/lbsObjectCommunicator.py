########################################################################
class ObjectCommunicator:
    """A class holding received and sent messages for an object
    """

    ####################################################################
    def __init__(self, r, s, i=None):
        
        # Index of object having this communicator if defined
        self.object_index = i

        # Map of communications received by object
        if isinstance(r, dict):
            self.received = r

        # Map of communications sent by object
        if isinstance(s, dict):
            self.sent = s

    ####################################################################
    def get_received(self):
        """Return all from_object=weight pairs received by object
        """

        return self.received

    ####################################################################
    def get_received_from(self, o):
        """Return the weight of message received from an object if any
        """

        return self.received.get(o)

    ####################################################################
    def get_sent(self):
        """Return all to_object=weight pairs sent from object
        """

        return self.sent

    ####################################################################
    def get_sent_to(self, o):
        """Return the weight of message received from an object if any
        """

        return self.sent.get(o)

    ####################################################################
    def check_and_summarize_one_way(self, direction, print_indent=None):
        """Summarize one-way communicator properties and check for errors
        """

        # Assert that direction is of known type
        if not direction in ("to", "from"):
            print("** ERROR: unknown direction string: {}".format(direction))
            sys.exit(1)

        # Initialize counter
        n = 0

        # Iterate over one-way communications
        communications = self.sent if direction == "to" else self.received
        for k, v in communications.items():
            # Sanity check
            if  k.get_id() == self.object_index:
                print("** ERROR: object {} cannot send communication to itself.".format(
                    self.object_index))
                sys.exit(1)

            # Update counter
            n += 1

            # Report current communicaton item if requested
            if print_indent:
                print("{}{} object {}: {}".format(
                    print_indent,
                    "->" if direction == "to" else "<-",
                    k.get_id(),
                    v))

        # Return counter
        return n

    ####################################################################
    def check_and_summarize(self, print_indent=None):
        """Summarize communicator properties and check for errors
        """

        # Check and summarize sent communications
        n_sent = self.check_and_summarize_one_way("to", print_indent)

        # Check and summarize received communications
        n_recv = self.check_and_summarize_one_way("from", print_indent)

        # Return counters
        return n_sent, n_recv

########################################################################
