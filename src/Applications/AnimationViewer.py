#!/usr/bin/env python2.7
#@HEADER
###############################################################################
AnimationViewer_module_aliases = {}
for m in [
    "os",
    "sys",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in AnimationViewer_module_aliases:
            globals()[AnimationViewer_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

import paraview.simple as pv
from ParaviewViewer    import ParaviewViewer

if __name__ == '__main__':
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ParaviewViewerBase     import ViewerParameters
        from ParaviewViewerBase     import ParaviewViewerBase
    else:
        from ..ParaviewViewerBase   import ViewerParameters
        from ..ParaviewViewerBase   import ParaviewViewerBase

###############################################################################
class AnimationViewer(ParaviewViewer):
    """A concrete class providing an Animation Viewer
    """

    ###########################################################################
    def __init__(self, file_name=None, viewer_type=None):

        # Call superclass init
        super(AnimationViewer, self).__init__(file_name, viewer_type)

    ###########################################################################
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
        print("[AnimationViewer] ###  Generating AVI animation...")
        pv.WriteAnimation(self.file_name+".avi",
                       Magnification=1,
                       Quality = 2,
                       FrameRate=1.0,
                       Compression=True)
        print("[AnimationViewer] ### AVI animation generated.")

###############################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print("[AnimationViewer] ### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print("[AnimationViewer] Parsing command line arguments")
    params = ViewerParameters()
    params.parse_command_line()
    animationViewer = ParaviewViewerBase.factory(params.file_name, "Animation")

    # Create view from AnimationViewer instance
    reader = animationViewer.createViews()

    # Save generated view
    animationViewer.saveView(reader)

    # If this point is reached everything went fine
    print("[AnimationViewer] {} file views generated ###".format(
        animationViewer.file_name))

###############################################################################
