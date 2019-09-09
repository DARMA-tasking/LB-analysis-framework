#
#@HEADER
###############################################################################
#
#                           lbsObjectCommunicator.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
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
