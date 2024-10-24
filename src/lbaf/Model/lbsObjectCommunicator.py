#
#@HEADER
###############################################################################
#
#                           lbsObjectCommunicator.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
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

    def get_max_volume(self):
        """Return the maximum bytes received or sent at this communicator."""
        max_received, max_sent = 0., 0.
        if len(self.__sent) > 0:
            max_sent = max(self.__sent.values())
        if len(self.__received) > 0:
            max_received = max(self.__received.values())
        return max(max_received, max_sent)

    def summarize(self) -> tuple:
        """Summarize communicator properties and check for errors."""
        # Summarize sent communications
        w_sent = self.__summarize_unidirectional("to")

        # Summarize received communications
        w_recv = self.__summarize_unidirectional("from")

        # Return counters
        return w_sent, w_recv
