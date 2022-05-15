# state file generated using paraview version 5.10.1

# uncomment the following three lines to ensure this script works in future versions
#import paraview
#paraview.compatibility.major = 5
#paraview.compatibility.minor = 10

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# ----------------------------------------------------------------
# setup views used in the visualization
# ----------------------------------------------------------------

# get the material library
materialLibrary1 = GetMaterialLibrary()

# Create a new 'Render View'
renderView1 = CreateView('RenderView')
renderView1.ViewSize = [1784, 1264]
renderView1.InteractionMode = '2D'
renderView1.AxesGrid = 'GridAxes3DActor'
renderView1.OrientationAxesVisibility = 0
renderView1.CenterOfRotation = [3.4999999552965164, 1.4999999552965164, 0.0]
renderView1.StereoType = 'Crystal Eyes'
renderView1.CameraPosition = [3.509172471628904, 1.509172471628904, 21.36271121092086]
renderView1.CameraFocalPoint = [3.509172471628904, 1.509172471628904, 0.0]
renderView1.CameraFocalDisk = 1.0
renderView1.CameraParallelScale = 3.02381481390261
renderView1.BackEnd = 'OSPRay raycaster'
renderView1.OSPRayMaterialLibrary = materialLibrary1

SetActiveView(None)

# ----------------------------------------------------------------
# setup view layouts
# ----------------------------------------------------------------

# create new layout object 'Layout #1'
layout1 = CreateLayout(name='Layout #1')
layout1.AssignView(0, renderView1)
layout1.SetSize(1784, 1264)

# ----------------------------------------------------------------
# restore active view
SetActiveView(renderView1)
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# setup the data processing pipelines
# ----------------------------------------------------------------

# create a new 'XML PolyData Reader'
output_file_object_view_0 = XMLPolyDataReader(registrationName='output_file_object_view_0*', FileName=['/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_00.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_01.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_02.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_03.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_04.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_05.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_06.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_07.vtp', '/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_object_view_08.vtp'])
output_file_object_view_0.CellArrayStatus = ['Volume']
output_file_object_view_0.PointArrayStatus = ['Time']
output_file_object_view_0.TimeArray = 'None'

# create a new 'Calculator'
calculator1 = Calculator(registrationName='Calculator1', Input=output_file_object_view_0)
calculator1.Function = 'sqrt(Time)'

# create a new 'IOSS Reader'
output_file_rank_viewe = IOSSReader(registrationName='output_file_rank_view.e', FileName=['/Users/pppebay/Documents/Git/LB-analysis-framework/output/output_file_rank_view.e'])
output_file_rank_viewe.ElementBlocks = ['block_3']
output_file_rank_viewe.NodeBlockFields = ['load', 'work']
output_file_rank_viewe.ElementBlockFields = ['largest_directed_volume']

# create a new 'Plot Global Variables Over Time'
plotGlobalVariablesOverTime1 = PlotGlobalVariablesOverTime(registrationName='PlotGlobalVariablesOverTime1', Input=output_file_rank_viewe)

# create a new 'Glyph'
glyph1 = Glyph(registrationName='Glyph1', Input=output_file_rank_viewe,
    GlyphType='2D Glyph')
glyph1.OrientationArray = ['POINTS', 'No orientation array']
glyph1.ScaleArray = ['POINTS', 'No scale array']
glyph1.ScaleFactor = 0.95
glyph1.GlyphTransform = 'Transform2'
glyph1.GlyphMode = 'All Points'

# init the '2D Glyph' selected for 'GlyphType'
glyph1.GlyphType.GlyphType = 'Square'
glyph1.GlyphType.Filled = 1

# create a new 'Glyph'
glyph2 = Glyph(registrationName='Glyph2', Input=calculator1,
    GlyphType='Sphere')
glyph2.OrientationArray = ['POINTS', 'No orientation array']
glyph2.ScaleArray = ['POINTS', 'Result']
glyph2.GlyphTransform = 'Transform2'
glyph2.GlyphMode = 'All Points'

# init the 'Sphere' selected for 'GlyphType'
glyph2.GlyphType.ThetaResolution = 32
glyph2.GlyphType.PhiResolution = 32

# create a new 'Threshold'
threshold1 = Threshold(registrationName='Threshold1', Input=output_file_object_view_0)
threshold1.Scalars = ['CELLS', 'Volume']
threshold1.LowerThreshold = 8000.0
threshold1.UpperThreshold = 591572.0

# ----------------------------------------------------------------
# setup the visualization in view 'renderView1'
# ----------------------------------------------------------------

# show data from glyph1
glyph1Display = Show(glyph1, renderView1, 'GeometryRepresentation')

# get color transfer function/color map for 'work'
workLUT = GetColorTransferFunction('work')
workLUT.AutomaticRescaleRangeMode = 'Never'
workLUT.RGBPoints = [0.018607455999217686, 0.231373, 0.298039, 0.752941, 0.06613309299980713, 0.865003, 0.865003, 0.865003, 0.11365873000039654, 0.705882, 0.0156863, 0.14902]
workLUT.ScalarRangeInitialized = 1.0

# trace defaults for the display properties.
glyph1Display.Representation = 'Surface'
glyph1Display.ColorArrayName = ['POINTS', 'work']
glyph1Display.LookupTable = workLUT
glyph1Display.Opacity = 0.5
glyph1Display.SelectTCoordArray = 'None'
glyph1Display.SelectNormalArray = 'None'
glyph1Display.SelectTangentArray = 'None'
glyph1Display.OSPRayScaleArray = 'load'
glyph1Display.OSPRayScaleFunction = 'PiecewiseFunction'
glyph1Display.SelectOrientationVectors = 'None'
glyph1Display.ScaleFactor = 0.7949999898672104
glyph1Display.SelectScaleArray = 'None'
glyph1Display.GlyphType = 'Arrow'
glyph1Display.GlyphTableIndexArray = 'None'
glyph1Display.GaussianRadius = 0.03974999949336052
glyph1Display.SetScaleArray = ['POINTS', 'load']
glyph1Display.ScaleTransferFunction = 'PiecewiseFunction'
glyph1Display.OpacityArray = ['POINTS', 'load']
glyph1Display.OpacityTransferFunction = 'PiecewiseFunction'
glyph1Display.DataAxesGrid = 'GridAxesRepresentation'
glyph1Display.PolarAxes = 'PolarAxesRepresentation'

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
glyph1Display.ScaleTransferFunction.Points = [0.015334740000000124, 0.0, 0.5, 0.0, 0.11871918099996748, 1.0, 0.5, 0.0]

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
glyph1Display.OpacityTransferFunction.Points = [0.015334740000000124, 0.0, 0.5, 0.0, 0.11871918099996748, 1.0, 0.5, 0.0]

# show data from output_file_object_view_0
output_file_object_view_0Display = Show(output_file_object_view_0, renderView1, 'GeometryRepresentation')

# get color transfer function/color map for 'Volume'
volumeLUT = GetColorTransferFunction('Volume')
volumeLUT.AutomaticRescaleRangeMode = 'Never'
volumeLUT.RGBPoints = [0.0, 1.0, 1.0, 1.0, 591572.0, 0.0, 0.0, 0.0]
volumeLUT.ColorSpace = 'RGB'
volumeLUT.NanColor = [1.0, 0.0, 0.0]
volumeLUT.NanOpacity = 0.0
volumeLUT.ScalarRangeInitialized = 1.0

# trace defaults for the display properties.
output_file_object_view_0Display.Representation = 'Surface'
output_file_object_view_0Display.ColorArrayName = ['CELLS', 'Volume']
output_file_object_view_0Display.LookupTable = volumeLUT
output_file_object_view_0Display.LineWidth = 5.0
output_file_object_view_0Display.SelectTCoordArray = 'None'
output_file_object_view_0Display.SelectNormalArray = 'None'
output_file_object_view_0Display.SelectTangentArray = 'None'
output_file_object_view_0Display.OSPRayScaleArray = 'Time'
output_file_object_view_0Display.OSPRayScaleFunction = 'PiecewiseFunction'
output_file_object_view_0Display.SelectOrientationVectors = 'None'
output_file_object_view_0Display.ScaleFactor = 0.769831332564354
output_file_object_view_0Display.SelectScaleArray = 'Time'
output_file_object_view_0Display.GlyphType = 'Arrow'
output_file_object_view_0Display.GlyphTableIndexArray = 'Time'
output_file_object_view_0Display.GaussianRadius = 0.0384915666282177
output_file_object_view_0Display.SetScaleArray = ['POINTS', 'Time']
output_file_object_view_0Display.ScaleTransferFunction = 'PiecewiseFunction'
output_file_object_view_0Display.OpacityArray = ['POINTS', 'Time']
output_file_object_view_0Display.OpacityTransferFunction = 'PiecewiseFunction'
output_file_object_view_0Display.DataAxesGrid = 'GridAxesRepresentation'
output_file_object_view_0Display.PolarAxes = 'PolarAxesRepresentation'

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
output_file_object_view_0Display.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 0.10344837900003512, 1.0, 0.5, 0.0]

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
output_file_object_view_0Display.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 0.10344837900003512, 1.0, 0.5, 0.0]

# show data from glyph2
glyph2Display = Show(glyph2, renderView1, 'GeometryRepresentation')

# get color transfer function/color map for 'Time'
timeLUT = GetColorTransferFunction('Time')
timeLUT.AutomaticRescaleRangeMode = 'Never'
timeLUT.RGBPoints = [1.545700900007317e-06, 1.0, 0.984314, 0.901961, 2.449770834002614e-06, 0.960784, 0.94902, 0.670588, 3.882625117900522e-06, 0.886275, 0.921569, 0.533333, 6.153546118239067e-06, 0.784314, 0.878431, 0.396078, 9.752713352292612e-06, 0.666667, 0.839216, 0.294118, 1.5457009000073173e-05, 0.556863, 0.8, 0.239216, 2.4497708340026143e-05, 0.431373, 0.760784, 0.160784, 3.882625117900521e-05, 0.317647, 0.721569, 0.113725, 6.153546118239067e-05, 0.211765, 0.678431, 0.082353, 9.752713352292612e-05, 0.109804, 0.631373, 0.05098, 0.00015457009000073186, 0.082353, 0.588235, 0.082353, 0.0002449770834002614, 0.109804, 0.54902, 0.152941, 0.0003882625117900525, 0.113725, 0.521569, 0.203922, 0.0006153546118239073, 0.117647, 0.490196, 0.243137, 0.0009752713352292611, 0.117647, 0.45098, 0.270588, 0.001545700900007317, 0.113725, 0.4, 0.278431, 0.0024497708340026144, 0.109804, 0.34902, 0.278431, 0.003882625117900525, 0.094118, 0.278431, 0.25098, 0.006153546118239073, 0.086275, 0.231373, 0.219608, 0.009752713352292611, 0.07451, 0.172549, 0.180392, 0.015457009000073171, 0.054902, 0.109804, 0.121569]
timeLUT.UseLogScale = 1
timeLUT.ColorSpace = 'Lab'
timeLUT.NanColor = [0.25, 0.0, 0.0]
timeLUT.NanOpacity = 0.0
timeLUT.ScalarRangeInitialized = 1.0

# trace defaults for the display properties.
glyph2Display.Representation = 'Surface'
glyph2Display.ColorArrayName = ['POINTS', 'Time']
glyph2Display.LookupTable = timeLUT
glyph2Display.SelectTCoordArray = 'None'
glyph2Display.SelectNormalArray = 'None'
glyph2Display.SelectTangentArray = 'None'
glyph2Display.OSPRayScaleArray = 'Result'
glyph2Display.OSPRayScaleFunction = 'PiecewiseFunction'
glyph2Display.SelectOrientationVectors = 'None'
glyph2Display.ScaleFactor = 0.7678832411766052
glyph2Display.SelectScaleArray = 'Result'
glyph2Display.GlyphType = 'Arrow'
glyph2Display.GlyphTableIndexArray = 'Result'
glyph2Display.GaussianRadius = 0.03839416205883026
glyph2Display.SetScaleArray = ['POINTS', 'Result']
glyph2Display.ScaleTransferFunction = 'PiecewiseFunction'
glyph2Display.OpacityArray = ['POINTS', 'Result']
glyph2Display.OpacityTransferFunction = 'PiecewiseFunction'
glyph2Display.DataAxesGrid = 'GridAxesRepresentation'
glyph2Display.PolarAxes = 'PolarAxesRepresentation'

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
glyph2Display.ScaleTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 0.3216339207857827, 1.0, 0.5, 0.0]

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
glyph2Display.OpacityTransferFunction.Points = [0.0, 0.0, 0.5, 0.0, 0.3216339207857827, 1.0, 0.5, 0.0]

# setup the color legend parameters for each legend in this view

# get color legend/bar for workLUT in view renderView1
workLUTColorBar = GetScalarBar(workLUT, renderView1)
workLUTColorBar.Orientation = 'Horizontal'
workLUTColorBar.WindowLocation = 'Any Location'
workLUTColorBar.Position = [0.24263244810826778, 0.8964556962025316]
workLUTColorBar.Title = 'Rank work'
workLUTColorBar.ComponentTitle = ''
workLUTColorBar.LabelFontSize = 14
workLUTColorBar.AutomaticLabelFormat = 0
workLUTColorBar.LabelFormat = '%-#6.2g'
workLUTColorBar.UseCustomLabels = 1
workLUTColorBar.CustomLabels = [7.0, 14.0, 21.0]
workLUTColorBar.RangeLabelFormat = '%-#6.2g'
workLUTColorBar.ScalarBarLength = 0.5000000000000001

# set color bar visibility
workLUTColorBar.Visibility = 1

# get color legend/bar for timeLUT in view renderView1
timeLUTColorBar = GetScalarBar(timeLUT, renderView1)
timeLUTColorBar.Orientation = 'Horizontal'
timeLUTColorBar.WindowLocation = 'Any Location'
timeLUTColorBar.Position = [0.5512359865470853, 0.03174050632911394]
timeLUTColorBar.Title = 'Object Time'
timeLUTColorBar.ComponentTitle = ''
timeLUTColorBar.LabelFontSize = 14
timeLUTColorBar.AutomaticLabelFormat = 0
timeLUTColorBar.LabelFormat = '%-#6.1g'
timeLUTColorBar.UseCustomLabels = 1
timeLUTColorBar.CustomLabels = [0.0001, 0.001, 0.01]
timeLUTColorBar.RangeLabelFormat = '%-#6.1g'
timeLUTColorBar.ScalarBarLength = 0.32999999999999996

# set color bar visibility
timeLUTColorBar.Visibility = 1

# get color legend/bar for volumeLUT in view renderView1
volumeLUTColorBar = GetScalarBar(volumeLUT, renderView1)
volumeLUTColorBar.Orientation = 'Horizontal'
volumeLUTColorBar.WindowLocation = 'Any Location'
volumeLUTColorBar.Position = [0.04675168161434995, 0.028575949367088474]
volumeLUTColorBar.Title = 'Inter-object volume'
volumeLUTColorBar.ComponentTitle = ''
volumeLUTColorBar.LabelFontSize = 14
volumeLUTColorBar.AutomaticLabelFormat = 0
volumeLUTColorBar.UseCustomLabels = 1
volumeLUTColorBar.CustomLabels = [300000.0]
volumeLUTColorBar.RangeLabelFormat = '%-#6.3g'
volumeLUTColorBar.ScalarBarLength = 0.3300000000000002

# set color bar visibility
volumeLUTColorBar.Visibility = 1

# show color legend
glyph1Display.SetScalarBarVisibility(renderView1, True)

# show color legend
output_file_object_view_0Display.SetScalarBarVisibility(renderView1, True)

# show color legend
glyph2Display.SetScalarBarVisibility(renderView1, True)

# ----------------------------------------------------------------
# setup color maps and opacity mapes used in the visualization
# note: the Get..() functions create a new object, if needed
# ----------------------------------------------------------------

# get opacity transfer function/opacity map for 'Time'
timePWF = GetOpacityTransferFunction('Time')
timePWF.Points = [0.0, 0.0, 0.5, 0.0, 0.015457009000073185, 1.0, 0.5, 0.0]
timePWF.ScalarRangeInitialized = 1

# get opacity transfer function/opacity map for 'Volume'
volumePWF = GetOpacityTransferFunction('Volume')
volumePWF.Points = [0.0, 0.0, 0.5, 0.0, 591572.0, 1.0, 0.5, 0.0]
volumePWF.ScalarRangeInitialized = 1

# get opacity transfer function/opacity map for 'work'
workPWF = GetOpacityTransferFunction('work')
workPWF.Points = [0.018607455999217686, 0.0, 0.5, 0.0, 0.11365873000039654, 1.0, 0.5, 0.0]
workPWF.ScalarRangeInitialized = 1

# ----------------------------------------------------------------
# restore active source
SetActiveSource(output_file_object_view_0)
# ----------------------------------------------------------------


if __name__ == '__main__':
    # generate extracts
    SaveExtracts(ExtractsOutputDirectory='extracts')