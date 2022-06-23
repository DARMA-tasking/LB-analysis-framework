import sys

import paraview.simple as pv

from lbaf.Applications.ParaviewViewer import ParaviewViewer
from lbaf.Applications.ParaviewViewerBase import ViewerParameters, ParaviewViewerBase
from lbaf.Utils.exception_handler import exc_handler
from lbaf.Utils.logger import logger


class AnimationViewer(ParaviewViewer):
    """ A concrete class providing an Animation Viewer
    """

    def __init__(self, exodus=None, file_name=None, viewer_type=None):
        # Call superclass init
        super().__init__(exodus, file_name, viewer_type)

        # Starting logger
        self.__logger = logger()

    def saveView(self, reader):
        """ Save animation
        """
        # Get animation scene
        animationScene = pv.GetAnimationScene()
        animationScene.PlayMode = "Snap To TimeSteps"

        # Save animation images
        for t in reader.TimestepValues.GetData()[:]:
            animationScene.AnimationTime = t

        # Save animation movie
        self.__logger.info("###  Generating AVI animation...")
        pv.AssignViewToLayout()
        pv.WriteAnimation(f"{self.file_name}.avi", Magnification=1, Quality=2, FrameRate=1.0, Compression=True)
        self.__logger.info(f"### AVI animation generated.")


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
        sys.excepthook = exc_handler
        raise SystemExit(1)

    # Check if arguments were correctly parsed
    animationViewer = ParaviewViewerBase.factory(params.exodus, params.file_name, "Animation")

    # Create view from AnimationViewer instance
    reader = animationViewer.createViews()

    # Save generated view
    animationViewer.saveView(reader)

    # If this point is reached everything went fine
    lgr.info(f"{animationViewer.file_name} file views generated ###")
