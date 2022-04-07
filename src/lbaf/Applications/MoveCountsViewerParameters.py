#
#@HEADER
###############################################################################
#
#                         MoveCountsViewerParameters.py
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
class MoveCountsViewerParameters:
    """A class to describe MoveCountsViewer parameters
    """

    def __init__(self, viewer):

        # Set parameters based on viewer's attribute values

        # Set renderer parameters
        self.renderer_background = [1, 1, 1]

        # Set actor_vertices parameters
        self.actor_vertices_screen_size = 50 if viewer.interactive else 5000
        self.actor_vertices_color = [0, 0, 0]
        self.actor_vertices_opacity = .3 if viewer.interactive else .5

        # Set actor_labels parameters
        self.actor_labels_color = [0, 0, 0]
        self.actor_labels_font_size = 16 if viewer.interactive else 150
        self.actor_edges_opacity = .5 if viewer.interactive else 1
        self.actor_edges_line_width = 2 if viewer.interactive else 15

        # Set actor_arrows parameters
        self.actor_arrows_edge_glyph_position = .5
        self.actor_arrows_source_scale = .075

        # Set actor_bar parameters
        self.actor_bar_number_of_labels = 2
        self.actor_bar_width = .2
        self.actor_bar_heigth = .08
        self.actor_bar_position = [.4, .91]
        self.actor_bar_title_color = [0, 0, 0]
        self.actor_bar_label_color = [0, 0, 0]

        # Set window parameters
        self.window_size_x = 600
        self.window_size_y = 600

        # Set wti (WindowToImageFilter) parameters
        self.wti_scale = 10
