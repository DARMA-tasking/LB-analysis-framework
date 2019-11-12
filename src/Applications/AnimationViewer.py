#!/usr/bin/env python2.7
#@HEADER
###############################################################################
AnimationViewer_module_aliases = {}
for m in [
    "bcolors",
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

try:
    import paraview.simple as pv
    globals()["has_paraview"] = True
except:
    globals()["has_paraview"] = False
    if not __name__ == '__main':
        print("[AnimationViewer] Failed to import paraview. Cannot save visual artifacts.")
        sys.exit(0)
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
    def __init__(self, exodus=None, file_name=None, viewer_type=None):

        # Call superclass init
        super(AnimationViewer, self).__init__(exodus, file_name, viewer_type)

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
        print(bcolors.HEADER
            + "[AnimationViewer] "
            + bcolors.END
            + "###  Generating AVI animation...")
        pv.WriteAnimation(self.file_name+".avi",
                       Magnification=1,
                       Quality = 2,
                       FrameRate=1.0,
                       Compression=True)
        print(bcolors.HEADER
            + "[AnimationViewer] "
            + bcolors.END
            + "### AVI animation generated.")

###############################################################################
if __name__ == '__main__':

    # Check if visualization library imported
    if not has_paraview:
        print(bcolors.ERR
            + "** ERROR: failed to import paraview. Cannot save visual artifacts.Exiting."
            + bcolors.END)
        sys.exit(1)

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

###############################################################################
