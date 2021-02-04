#
#@HEADER
###############################################################################
#
#                              PNGViewer.py
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
import sys

import bcolors

import paraview.simple as pv

from src.Applications.ParaviewViewer import ParaviewViewer
from src.Applications.ParaviewViewerBase import ViewerParameters, ParaviewViewerBase


class PNGViewer(ParaviewViewer):
    """A concrete class providing a PNG Viewer
    """

    def __init__(self, exodus=None, file_name=None, viewer_type=None):

        # Call superclass init
        super(PNGViewer, self).__init__(exodus, file_name, viewer_type)

    def saveView(self, reader):
        """Save figure
        """

        # Get animation scene
        animationScene = pv.GetAnimationScene()
        animationScene.PlayMode = "Snap To TimeSteps"

        # Save animation images
        print(bcolors.HEADER
            + "[PNGViewer] "
            + bcolors.END
            + "###  Generating PNG images...")
        for t in reader.TimestepValues.GetData()[:]:
            animationScene.AnimationTime = t
            pv.WriteImage(self.file_name + ".%f.png" % t);
        print(bcolors.HEADER
            + "[PNGViewer] "
            + bcolors.END
            + "### All PNG images generated.")


if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print(bcolors.HEADER
        + "[PNGViewer] "
        + bcolors.END
        + "### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print(bcolors.HEADER
        + "[PNGViewer] "
        + bcolors.END
        + "Parsing command line arguments")
    params = ViewerParameters()
    if params.parse_command_line():
        sys.exit(1)
    pngViewer = ParaviewViewerBase.factory(params.exodus, params.file_name, "PNG")

    # Create view from PNGViewer instance
    reader = pngViewer.createViews()

    # Save generated view
    pngViewer.saveView(reader)

    # If this point is reached everything went fine
    print(bcolors.HEADER
        + "[PNGViewer] "
        + bcolors.END
        + "{} file views generated ###".format(pngViewer.file_name))
