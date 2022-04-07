#
#@HEADER
###############################################################################
#
#                              ParaviewViewer.py
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

from lbaf.Applications.ParaviewViewerBase import ViewerParameters, ParaviewViewerBase
from lbaf.Utils.logger import logger


class ParaviewViewer(ParaviewViewerBase):
    """ A concrete class providing a Paraview Viewer
    """

    def __init__(self, exodus=None, file_name=None, viewer_type=None):

        # Call superclass init
        super(ParaviewViewer, self).__init__(exodus, file_name, viewer_type)

    def saveView(self, reader):
        """ Save figure
        """
        from lbaf.Applications.AnimationViewer import AnimationViewer
        from lbaf.Applications.PNGViewer import PNGViewer
        self.__class__ = PNGViewer
        self.saveView(reader)
        self.__class__ = AnimationViewer
        self.saveView(reader)


if __name__ == '__main__':
    # Assign logger to variable
    lgr = logger()

    # Print startup information
    sv = sys.version_info
    lgr.info(f"### Started with Python {sv.major}.{sv.minor}.{sv.micro}")

    # Instantiate parameters and set values from command line arguments
    lgr.info("Parsing command line arguments")
    params = ViewerParameters()
    if params.parse_command_line():
        sys.exit(1)
    viewer = ParaviewViewerBase.factory(params.exodus, params.file_name, "")

    # Create view from PNGViewer instance
    reader = viewer.createViews()

    from lbaf.Applications.AnimationViewer import AnimationViewer
    from lbaf.Applications.PNGViewer import PNGViewer
    # Save generated view
    viewer.__class__ = PNGViewer
    viewer.saveView(reader)
    viewer.__class__ = AnimationViewer
    viewer.saveView(reader)

    # If this point is reached everything went fine
    lgr.info(f"{viewer.file_name} file views generated ###")
