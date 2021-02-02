#
#@HEADER
###############################################################################
#
#                              ParaviewViewerBase.py
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
import abc
import getopt
import importlib
import sys

import bcolors

try:
    import paraview.simple as pv
    globals()["has_paraview"] = True
except:
    globals()["has_paraview"] = False
    if not __name__ == '__main':
        print("*  WARNING: Failed to import paraview. Cannot save visual artifacts.")
        sys.exit(0)


class ViewerParameters:
    """A class to describe ParaviewViewerBase parameters
    """

    def usage(self):
        """Provide online help
        """

        print("Usage:")
        print("\t [-e]        ExodusII file name")
        print("\t [-f]        visualization file name")
        print("\t [-h]        help: print this message and exit")
        print('')

    def parse_command_line(self):
        """Parse command line
        """
        # Check if visualization library imported
        if not has_paraview:
            print(bcolors.ERR
                  + "** ERROR: failed to import paraview. Cannot save visual artifacts.Exiting."
                  + bcolors.END)
            sys.exit(1)

        # Try to hash command line with respect to allowable flags
        try:
            opts, args = getopt.getopt(sys.argv[1:], "he:f:")

        except getopt.GetoptError:
            print(bcolors.ERR
                + "** ERROR: incorrect command line arguments."
                + bcolors.END)
            self.usage()
            return True

        # Parse arguments and assign corresponding member variable values
        for o, a in opts:
            if o == "-h":
                self.usage()
                sys.exit(0)
            elif o == "-e":
                self.exodus = a
            elif o == "-f":
                self.file_name = a

        # Ensure that exactly one ExodusII file has been provided
        if not self.exodus:
            print(bcolors.ERR
                + "** ERROR: Provide an ExodusII file"
                + bcolors.END)
            return True

        # Set default visualization file name prefix
        if not self.file_name:
            self.file_name = self.exodus

        # Set viewer type
        self.viewer_type = None

        # Set material library
        self.material_library = pv.GetMaterialLibrary()

        # No line parsing error occurred
        return False


class ParaviewViewerBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, exodus=None, file_name=None, viewer_type=None):

        # Check if visualization library imported
        if not has_paraview:
            print(bcolors.ERR
                  + "** ERROR: failed to import paraview. Cannot save visual artifacts.Exiting."
                  + bcolors.END)
            sys.exit(1)

        # ExodusII file to be displayed
        self.exodus = "{}.e".format(exodus)

        # visualization file name
        self.file_name = "{}.e".format(file_name)

        # Viewer type
        self.viewer_type = viewer_type

        # Material library
        self.material_library = pv.GetMaterialLibrary()

    @staticmethod
    def factory(exodus, file_name, viewer_type):
        """Produce the necessary concrete backend instance
        """

        # Unspecified ExodusII file name
        if not exodus:
            print(bcolors.ERR
                + "** ERROR: an ExodusII file name needs to be provided. Exiting."
                + bcolors.END)
            sys.exit(1)

        # Unspecified visualization file name
        if (not file_name) or file_name == "''":
            print(bcolors.WARN
                + "** WARNING: visualization file name has not been provided. "
                  "Using ExodusII file name by default."
                + bcolors.END)
            file_name = exodus

        # PNG viewer
        if viewer_type == "PNG":
            try:
                PNGViewer = getattr(importlib.import_module("PNGViewer"),
                    "PNGViewer")
                ret_object = PNGViewer(exodus, file_name, viewer_type)
            except:
                ret_object = None

        # Animation viewer
        elif viewer_type == "Animation":
            try:
                AnimationViewer = getattr(importlib.import_module("AnimationViewer"),
                    "AnimationViewer")
                ret_object = AnimationViewer(exodus, file_name, viewer_type)
            except:
                ret_object = None

        # Paraview viewer
        elif viewer_type == "":
            try:
                ParaviewViewer = getattr(importlib.import_module("ParaviewViewer"),
                    "ParaviewViewer")
                ret_object = ParaviewViewer(exodus, file_name)
            except:
                ret_object = None

        # Unspecified viewer type
        elif viewer_type == None:
            print(bcolors.ERR
                + "** ERROR: a viewer type needs to be provided. Exiting."
                + bcolors.END)
            sys.exit(1)

        # Unsupported viewer type
        else:
            print(bcolors.ERR
                + "** ERROR: {} type viewer unsupported. Exiting.".format(viewer_type)
                + bcolors.END)
            sys.exit(1)

        # Report not instantiated
        if not ret_object:
            print(bcolors.ERR
                + "** ERROR: {} viewer not instantiated. Exiting.".format(viewer_type)
                + bcolors.END)
            sys.exit(1)

        # Return instantiated object
        ret_object.exodus = "{}.e".format(exodus)
        ret_object.file_name = "{}.e".format(file_name)
        ret_object.viewer_type = viewer_type
        ret_object.material_library = pv.GetMaterialLibrary()
        print(bcolors.HEADER
            + "[ParaviewViewerBase] "
            + bcolors.END
            + "Instantiated {} viewer.".format(viewer_type))
        return ret_object

    def get_exodus(self):
        """Convenience method to get ExodusII file name
        """

        # Return value of ExodusII file name
        return self.exodus

    def get_file_name(self):
        """Convenience method to get visualization file name
        """

        # Return value of visualization file name
        return self.file_name

    def get_viewer_type(self):
        """Convenience method to get viewer type
        """

        # Return value of viewer type
        return self.viewer_type

    def createRenderView(self,
                         view_size=[1024, 1024]):
        """Create a new 'Render View'
        """

        renderView = pv.CreateView('RenderView')
        if view_size:
            renderView.ViewSize = view_size
        renderView.InteractionMode = '2D'
        renderView.AxesGrid = 'GridAxes3DActor'
        renderView.OrientationAxesVisibility = 0
        renderView.CenterOfRotation = [1.5, 1.5, 0.0]
        renderView.StereoType = 0
        renderView.CameraPosition = [1.5, 1.5, 10000.0]
        renderView.CameraFocalPoint = [1.5, 1.5, 0.0]
        renderView.CameraParallelScale = 2.1213203435596424
        renderView.CameraParallelProjection = 1
        renderView.Background = [1.0, 1.0, 1.0]
        renderView.OSPRayMaterialLibrary = self.material_library

        # init the 'GridAxes3DActor' selected for 'AxesGrid'
        renderView.AxesGrid.XTitleFontFile = ''
        renderView.AxesGrid.YTitleFontFile = ''
        renderView.AxesGrid.ZTitleFontFile = ''
        renderView.AxesGrid.XLabelFontFile = ''
        renderView.AxesGrid.YLabelFontFile = ''
        renderView.AxesGrid.ZLabelFontFile = ''

        return renderView

    def createExodusIIReader(self, elt_var, pt_var):
        """Create a new 'ExodusIIReader'
        """

        reader = pv.ExodusIIReader(FileName=[self.exodus])
        reader.GenerateObjectIdCellArray = 0
        reader.GenerateGlobalElementIdArray = 0
        reader.ElementVariables = [elt_var]
        reader.GenerateGlobalNodeIdArray = 0
        reader.PointVariables = [pt_var]
        reader.GlobalVariables = []
        reader.ElementBlocks = ['Unnamed block ID: 3 Type: edge']

        return reader

    def createCalculator(self, reader, fct, var):
        """Create a new 'Calculator'
        """

        calculator = pv.Calculator(Input=reader)
        calculator.ResultArrayName = "{}_{}".format(fct, var.lower())
        calculator.Function = "{}({})".format(fct, var)

        return calculator

    def createGlyph(self, input, type='Box', factor=0.1, mode="All Points"):
        """Create a new 'Glyph'
        """

        glyph = pv.Glyph(Input=input, GlyphType=type)
        glyph.OrientationArray = ['POINTS', 'No orientation array']
        glyph.ScaleArray = ['POINTS', '{}'.format(input.ResultArrayName)]
        glyph.ScaleFactor = factor
        glyph.GlyphTransform = 'Transform2'
        glyph.GlyphMode = mode

        return glyph

    def createColorTransferFunction(self,
                                    var,
                                    colors=None,
                                    nan_color=[1.,1.,1.],
                                    nan_opacity=None,
                                    auto_rescale_range_mode="Never"):
        """Create a color transfer function/color map
        """

        # get color transfer function/color map
        fct = pv.GetColorTransferFunction(var)
        if auto_rescale_range_mode:
            fct.AutomaticRescaleRangeMode = auto_rescale_range_mode
        if colors:
            fct.RGBPoints = colors
        if nan_color:
            fct.NanColor = nan_color
        if nan_opacity is not None:
            fct.NanOpacity = nan_opacity
        fct.ScalarRangeInitialized = 1.0

        return fct

    def createOpacityTransferFunction(self, var, points=None):
        """Create an opacity transfer function/color map
        """

        # get color transfer function/color map
        fct = pv.GetOpacityTransferFunction(var)
        if points:
            fct.Points = points
        fct.ScalarRangeInitialized = 1

        return fct

    def createDisplay(self,
                      reader,
                      renderView,
                      array_name,
                      color_transfert_fct,
                      line_width=None,
                      scale_factor=0.3,
                      glyph_type="Box",
                      opacity_fct=None):
        """Create a 'Display'
        """

        # Show data from reader
        display = pv.Show(reader, renderView)

        display.Representation = 'Surface'
        display.ColorArrayName = array_name
        display.LookupTable = color_transfert_fct
        if line_width:
            display.LineWidth = line_width
        display.OSPRayScaleArray = 'Load'
        display.OSPRayScaleFunction = 'PiecewiseFunction'
        display.SelectOrientationVectors = 'Load'
        if scale_factor:
            display.ScaleFactor = scale_factor
        display.SelectScaleArray = 'Load'
        if glyph_type:
            display.GlyphType = glyph_type
        display.GlyphTableIndexArray = 'Load'
        display.GaussianRadius = 0.015
        display.SetScaleArray = array_name
        display.ScaleTransferFunction = 'PiecewiseFunction'
        display.OpacityArray = array_name
        display.OpacityTransferFunction = 'PiecewiseFunction'
        display.DataAxesGrid = 'GridAxesRepresentation'
        display.SelectionCellLabelFontFile = ''
        display.SelectionPointLabelFontFile = ''
        display.PolarAxes = 'PolarAxesRepresentation'
        if opacity_fct:
            display.ScalarOpacityFunction = opacity_fct
            display.ScalarOpacityUnitDistance = 0.8601532551232605

        # init the 'GridAxesRepresentation' selected for 'DataAxesGrid'
        display.DataAxesGrid.XTitleFontFile = ''
        display.DataAxesGrid.YTitleFontFile = ''
        display.DataAxesGrid.ZTitleFontFile = ''
        display.DataAxesGrid.XLabelFontFile = ''
        display.DataAxesGrid.YLabelFontFile = ''
        display.DataAxesGrid.ZLabelFontFile = ''

        # init the 'PolarAxesRepresentation' selected for 'PolarAxes'
        display.PolarAxes.PolarAxisTitleFontFile = ''
        display.PolarAxes.PolarAxisLabelFontFile = ''
        display.PolarAxes.LastRadialAxisTextFontFile = ''
        display.PolarAxes.SecondaryRadialAxesTextFontFile = ''

        return display

    @abc.abstractmethod
    def saveView(self, reader):
        """Save view
        """

        pass

    def createViews(self):
        """Create views
        """
        # Disable automatic camera reset on 'Show'
        pv._DisableFirstRenderCameraReset()

        # Create render view
        renderView = self.createRenderView([900, 900])

        # Activate render view
        pv.SetActiveView(renderView)

        # Create ExodusII reader
        reader = self.createExodusIIReader("Weight", "Load")

        # Create sqrt(load) calculator to optimize visuals
        sqrt_load = self.createCalculator(reader, "sqrt", "Load")

        # Create sqrt(load) glyph
        glyph = self.createGlyph(sqrt_load, factor=0.05)

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
        weightLUT = self.createColorTransferFunction(
            "Weight",
            weight_colors,
            [1., 1., 1.],
            0.0)
        weightPWF = self.createOpacityTransferFunction(
            "Weight",
            weight_points)

        readerDisplay = self.createDisplay(
            reader,
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
        loadLUT = self.createColorTransferFunction(
            "Load",
            load_colors,
            [1.,1.,1.],
            None,
            "Never")
        loadPWF = self.createOpacityTransferFunction(
            "Load",
            load_points)

        # Create displays
        glyphDisplay = self.createDisplay(
            glyph,
            renderView,
            ['POINTS', 'Load'],
            loadLUT,
            None,
            0.005)

        # Activate glyph source
        pv.SetActiveSource(glyph)

        return reader
