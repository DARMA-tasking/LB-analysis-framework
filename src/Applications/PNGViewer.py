#
#!/usr/bin/env python2.7
#@HEADER
###############################################################################
PNGViewer_module_aliases = {}
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
        if m in PNGViewer_module_aliases:
            globals()[PNGViewer_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

import paraview.simple as pv
from ParaviewViewer import ParaviewViewer

########################################################################
class PNGViewer(ParaviewViewer):
    """A concrete class providing a PNG Viewer
    """

    ####################################################################
    def __init__(self):

        # Call superclass init
        super(ParaviewViewer, self).__init__()

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
        self.viewer_type = "PNG"

        # Set material library
        self.material_library = pv.GetMaterialLibrary()

        # No line parsing error occurred
        return False

    ####################################################################
    def saveView(self, reader):
        """Save figure
        """

        # Get animation scene
        animationScene = pv.GetAnimationScene()
        animationScene.PlayMode = "Snap To TimeSteps"

        # Save animation images
        print("[PNGViewer] ###  Generating PNG images...")
        for t in reader.TimestepValues.GetData()[:]:
            animationScene.AnimationTime = t
            pv.WriteImage(self.file_name + ".%f.png" % t);
        print("[PNGViewer] ### All PNG images generated.")

#######################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print("[PNGViewer] ### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro))

    # Instantiate parameters and set values from command line arguments
    print("[PNGViewer] Parsing command line arguments")

    pngViewer = PNGViewer()
    if pngViewer.parse_command_line():
        sys.exit(1)
    # viewer = ParaviewViewer.factory(pngViewer)

    # Disable automatic camera reset on 'Show'
    pv._DisableFirstRenderCameraReset()

    # Create render view
    renderView = pngViewer.createRenderView([900, 900])

    # Activate render view
    pv.SetActiveView(renderView)

    # Create ExodusII reader
    reader = pngViewer.createExodusIIReader("Weight", "Load")

    # Create sqrt(load) calculator to optimize visuals
    sqrt_load = pngViewer.createCalculator(reader, "sqrt", "Load")

    # Create sqrt(load) glyph
    glyph = pngViewer.createGlyph(sqrt_load,
                                  factor=0.05)

    # Instantiate weight colors and points
    weight_colors = [223.48540319420192,
                     0.231373,
                     0.298039,
                     0.752941,
                     784.8585271892204,
                     0.865003,
                     0.865003,
                     0.865003,
                     1346.2316511842387,
                     0.705882,
                     0.0156863,
                     0.14902]
    weight_points = [223.48540319420192,
                     0.0,
                     0.5,
                     0.0,
                     1346.2316511842387,
                     1.0,
                     0.5,
                     0.0]
    # Create color transfert functions
    weightLUT = pngViewer.createColorTransferFunction("Weight", weight_colors, [1., 1., 1.], 0.0)
    weightPWF = pngViewer.createOpacityTransferFunction("Weight", weight_points)

    readerDisplay = pngViewer.createDisplay(reader,
                                            renderView,
                                            ['CELLS', 'Weight'],
                                            weightLUT,
                                            4.0,
                                            None,
                                            None,
                                            weightPWF)

    # Instantiate load colors and points
    load_colors = [0.0,
                   0.231373,
                   0.298039,
                   0.752941,
                   130.73569142337513,
                   0.865003,
                   0.865003,
                   0.865003,
                   261.47138284675026,
                   0.705882,
                   0.0156863,
                   0.14902]
    load_points = [0.0,
                   0.0,
                   0.5,
                   0.0,
                   261.47138284675026,
                   1.0,
                   0.5,
                   0.0]

    # Create color transfert functions
    loadLUT = pngViewer.createColorTransferFunction("Load", load_colors, [1.,1.,1.], None, "Never")
    loadPWF = pngViewer.createOpacityTransferFunction("Load", load_points)

    # Create displays
    glyphDisplay = pngViewer.createDisplay(glyph,
                                           renderView,
                                           ['POINTS', 'Load'],
                                           loadLUT,
                                           None,
                                           0.005)

    # Activate glyph source
    pv.SetActiveSource(glyph)

    # Save view
    pngViewer.saveView(reader)

    # If this point is reached everything went fine
    print("[PNGViewer] {} file views generated ###".format(pngViewer.file_name))

########################################################################
