import sys

import paraview.simple as pv

from lbaf.Applications.ParaviewViewer import ParaviewViewer
from lbaf.Applications.ParaviewViewerBase import ViewerParameters, ParaviewViewerBase
from lbaf.Utils.logger import logger


class PNGViewer(ParaviewViewer):
    """ A concrete class providing a PNG Viewer
    """

    def __init__(self, exodus=None, file_name=None, viewer_type=None):

        # Call superclass init
        super(PNGViewer, self).__init__(exodus, file_name, viewer_type)

        # Starting logger
        self.__logger = logger()

    def saveView(self, reader):
        """ Save figure
        """

        # Get animation scene
        animationScene = pv.GetAnimationScene()
        animationScene.PlayMode = "Snap To TimeSteps"

        # Save animation images
        self.__logger.info("###  Generating PNG images...")
        for t in reader.TimestepValues.GetData()[:]:
            animationScene.AnimationTime = t
            pv.WriteImage(f"{self.file_name}.{t:.6f}.png")

        self.__logger.info("### All PNG images generated.")


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
    pngViewer = ParaviewViewerBase.factory(params.exodus, params.file_name, "PNG")

    # Create view from PNGViewer instance
    reader = pngViewer.createViews()

    # Save generated view
    pngViewer.saveView(reader)

    # If this point is reached everything went fine
    lgr.info(f"{pngViewer.file_name} file views generated ###")
