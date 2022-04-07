#
#@HEADER
###############################################################################
#
#                                 lbsObject.py
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

from src.Model.lbsObjectCommunicator import ObjectCommunicator


class Object:
    """ A class representing an object with time and communicator
    """
    def __init__(self, i: int, t: float, p: int = None, c: ObjectCommunicator = None):
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
