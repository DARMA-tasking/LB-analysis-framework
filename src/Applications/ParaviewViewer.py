#!/usr/bin/env python2.7
#@HEADER#
###############################################################################
ParaviewViewer_module_aliases = {}
for m in [
    "os",
    "pickle",
    "sys",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in ParaviewViewer_module_aliases:
            globals()[ParaviewViewer_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from ParaviewViewerBase import ViewerParameters
from ParaviewViewerBase import ParaviewViewerBase

if __name__ == '__main__':
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from PNGViewer              import PNGViewer
        from AnimationViewer        import AnimationViewer
    else:
        from ..PNGViewer            import PNGViewer
        from ..AnimationViewer      import AnimationViewer

###############################################################################
class ParaviewViewer(ParaviewViewerBase):
    """A concrete class providing a Paraview Viewer
    """

    ###########################################################################
    def __init__(self, file_name=None, viewer_type=None):

        # Call superclass init
        super(ParaviewViewer, self).__init__(file_name, viewer_type)

    ###########################################################################
    def saveView(self, reader):
        """Save figure
        """

        # Save images
        from PNGViewer              import PNGViewer
        from AnimationViewer        import AnimationViewer
        self.__class__ = PNGViewer
        self.saveView(reader)
        self.__class__ = AnimationViewer
        self.saveView(reader)

###############################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print("[ParaviewViewer] ### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print("[ParaviewViewer] Parsing command line arguments")
    params = ViewerParameters()
    params.parse_command_line()
    viewer = ParaviewViewerBase.factory(params.file_name, "")

    # Create view from PNGViewer instance
    reader = viewer.createViews()

    # Save generated view
    viewer.__class__ = PNGViewer
    viewer.saveView(reader)
    viewer.__class__ = AnimationViewer
    viewer.saveView(reader)

    # If this point is reached everything went fine
    print("[ParaviewViewer] {} file views generated ###".format(viewer.file_name))

###############################################################################
