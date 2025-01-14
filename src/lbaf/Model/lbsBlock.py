#
#@HEADER
###############################################################################
#
#                                 lbsBlock.py
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
class Block:
    """A class representing a memory block with footprint and home."""

    def __init__(
            self,
            b_id: int,
            h_id: int,
            size: float = 0.0,
            o_ids: set = None):

        if o_ids is None:
            o_ids = set()

        # Block index
        self.__index = int(b_id)

        # Rank to which block is initially assigned
        self.__home_id = int(h_id)

        # Nonnegative size required to for memory footprint of this block
        if not isinstance(size, float) or size < 0.0:
            raise TypeError(
                f"size: incorrect type {type(size)} or value: {size}")
        self.__size = size

        # Possibly empty set of objects initially attached to block
        if not isinstance(o_ids, set):
            raise TypeError(
                f"o_ids: incorrect type {type(o_ids)}")
        self.__attached_object_ids = o_ids

    def __repr__(self):
        return (
            f"<Block id: {self.__index}, home id: {self.__home_id}, "
            f"size: {self.__size}, object ids: {self.__attached_object_ids}>"
        )

    def get_id(self) -> int:
        """Return block ID."""
        return self.__index

    def get_home_id(self) -> int:
        """Return block home ID."""
        return self.__home_id

    def get_size(self) -> float:
        """Return block size."""
        return self.__size

    def detach_object_id(self, o_id: int) -> int:
        """Try to detach object ID from block and return length."""
        try:
            self.__attached_object_ids.remove(o_id)
        except Exception as err:
            raise TypeError(
                f"object id {o_id} is not attached to block {self.get_id()}") from err
        return len(self.__attached_object_ids)

    def attach_object_id(self, o_id: int):
        """Attach object ID to block."""
        self.__attached_object_ids.add(o_id)
