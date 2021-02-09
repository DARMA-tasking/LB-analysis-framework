#
#@HEADER
###############################################################################
#
#                              AnimationViewer.py
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
# This script was written by Philippe P. Pebay, NexGen Analytics LC 2019
# Please do not redistribute without permission
#
###############################################################################
import sys

import bcolors

import paraview.simple as pv

from src.Applications.ParaviewViewer import ParaviewViewer
from src.Applications.ParaviewViewerBase import ViewerParameters, ParaviewViewerBase


class AnimationViewer(ParaviewViewer):
    """A concrete class providing an Animation Viewer
    """

    def __init__(self, exodus=None, file_name=None, viewer_type=None):

        # Call superclass init
        super().__init__(exodus, file_name, viewer_type)

    def saveView(self, reader):
        """Save animation
        """

        # Get animation scene
        animationScene = pv.GetAnimationScene()
        animationScene.PlayMode = "Snap To TimeSteps"

        # Save animation images
        for t in reader.TimestepValues.GetData()[:]:
            animationScene.AnimationTime = t

        # Save animation movie
        print(bcolors.HEADER
            + "[AnimationViewer] "
            + bcolors.END
            + "###  Generating AVI animation...")
        pv.AssignViewToLayout()
        pv.WriteAnimation(f"{self.file_name}.avi", Magnification=1, Quality=2, FrameRate=1.0, Compression=True)
        print(bcolors.HEADER
            + "[AnimationViewer] "
            + bcolors.END
            + "### AVI animation generated.")


if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print(bcolors.HEADER
        + "[AnimationViewer] "
        + bcolors.END
        + "### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print(bcolors.HEADER
        + "[AnimationViewer] "
        + bcolors.END
        + "Parsing command line arguments")
    params = ViewerParameters()
    if params.parse_command_line():
        sys.exit(1)

    # Check if arguments were correctly parsed
    animationViewer = ParaviewViewerBase.factory(params.exodus, params.file_name, "Animation")

    # Create view from AnimationViewer instance
    reader = animationViewer.createViews()

    # Save generated view
    animationViewer.saveView(reader)

    # If this point is reached everything went fine
    print(bcolors.HEADER
        + "[AnimationViewer] "
        + bcolors.END
        + "{} file views generated ###".format(
        animationViewer.file_name))
