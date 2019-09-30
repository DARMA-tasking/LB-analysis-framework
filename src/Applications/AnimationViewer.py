#
#!/usr/bin/env python2.7
#@HEADER
###############################################################################
AnimationViewer_module_aliases = {}
for m in [
    "abc",
    "importlib",
    "getopt",
    "os",
    "sys"
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
from ParaviewViewerBase import ParaviewViewerBase

########################################################################
class AnimationViewer(ParaviewViewerBase):
    """A concrete class providing an Animation Viewer
    """

    ####################################################################
    def __init__(self):

        # Call superclass init
        super(ParaviewViewerBase, self).__init__()
    ####################################################################
    def usage(self):
        """Provide online help
        """

        print("Usage:")
        print("\t [-f]        ExodusII file name")
        print("\t [-h]        help: print this message and exit")
        print('')

    ####################################################################
    def parse_command_line(self):
        """Parse command line
        """

        # Try to hash command line with respect to allowable flags
        try:
            opts, args = getopt.getopt(sys.argv[1:], "f:")
        except getopt.GetoptError:
            print("** ERROR: incorrect command line arguments.")
            self.usage()
            return True

        # Parse arguments and assign corresponding member variable values
        for o, a in opts:
            if o == "-f":
                self.file_name = a

        # Ensure that exactly one ExodusII file has been provided
        if not self.file_name:
            print("** ERROR: Provide an ExodusII file")
            return True

        # Set viewer type
        self.viewer_type = "Animation"

        # Set material library
        self.material_library = pv.GetMaterialLibrary()

        # No line parsing error occurred
        return False

    ####################################################################
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

########################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print("[AnimationViewer] ### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print("[AnimationViewer] Parsing command line arguments")
    animationViewer = AnimationViewer()
    if animationViewer.parse_command_line():
        sys.exit(1)

    # Create view from AnimationViewer instance
    reader = animationViewer.createViews()

    # Save generated view
    animationViewer.saveView(reader)

    # If this point is reached everything went fine
    print("[AnimationViewer] {} file views generated ###".format(animationViewer.file_name))

########################################################################
