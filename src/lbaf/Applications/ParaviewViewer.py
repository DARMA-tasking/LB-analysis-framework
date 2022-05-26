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
        raise SystemExit(1)
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
