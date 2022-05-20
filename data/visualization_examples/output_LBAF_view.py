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

# Create a new 'Line Chart View'
lineChartView1 = CreateView('XYChartView')
lineChartView1.ViewSize = [882, 594]
lineChartView1.LegendPosition = [643, 1211]
lineChartView1.LeftAxisRangeMinimum = 0.06
lineChartView1.LeftAxisRangeMaximum = 0.115
lineChartView1.BottomAxisRangeMaximum = 8.0
lineChartView1.RightAxisRangeMaximum = 6.66
lineChartView1.TopAxisRangeMaximum = 6.66

# Create a new 'Line Chart View'
lineChartView2 = CreateView('XYChartView')
lineChartView2.ViewSize = [882, 594]
lineChartView2.LegendPosition = [634, 541]
lineChartView2.LeftAxisRangeMaximum = 1.1
lineChartView2.BottomAxisRangeMaximum = 8.0
lineChartView2.RightAxisRangeMaximum = 6.66
lineChartView2.TopAxisRangeMaximum = 6.66

# Create a new 'Line Chart View'
lineChartView3 = CreateView('XYChartView')
lineChartView3.ViewSize = [882, 592]
lineChartView3.LeftAxisRangeMinimum = 1.79
lineChartView3.LeftAxisRangeMaximum = 1.92
lineChartView3.BottomAxisRangeMaximum = 8.0
lineChartView3.RightAxisRangeMaximum = 6.66
lineChartView3.TopAxisRangeMaximum = 6.66

# Create a new 'Line Chart View'
lineChartView4 = CreateView('XYChartView')
lineChartView4.ViewSize = [882, 592]
lineChartView4.LeftAxisRangeMaximum = 1100000.0
lineChartView4.BottomAxisRangeMaximum = 8.0
lineChartView4.RightAxisRangeMaximum = 6.66
lineChartView4.TopAxisRangeMaximum = 6.66

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

# create new layout object 'Layout #2'
layout2 = CreateLayout(name='Layout #2')
layout2.SplitHorizontal(0, 0.500000)
layout2.SplitVertical(1, 0.500000)
layout2.AssignView(3, lineChartView1)
layout2.AssignView(4, lineChartView4)
layout2.SplitVertical(2, 0.500000)
layout2.AssignView(5, lineChartView2)
layout2.AssignView(6, lineChartView3)
layout2.SetSize(1765, 1187)

# ----------------------------------------------------------------
# restore active view
SetActiveView(lineChartView2)
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

# create a new 'Glyph'
glyph2 = Glyph(registrationName='Glyph2', Input=calculator1,
    GlyphType='Sphere')
glyph2.OrientationArray = ['POINTS', 'No orientation array']
glyph2.ScaleArray = ['POINTS', 'Result']
glyph2.ScaleFactor = 1.5
glyph2.GlyphTransform = 'Transform2'
glyph2.GlyphMode = 'All Points'

# init the 'Sphere' selected for 'GlyphType'
glyph2.GlyphType.ThetaResolution = 32
glyph2.GlyphType.PhiResolution = 32

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

# create a new 'Plot Global Variables Over Time'
plotGlobalVariablesOverTime1 = PlotGlobalVariablesOverTime(registrationName='PlotGlobalVariablesOverTime1', Input=output_file_rank_viewe)

# create a new 'Threshold'
threshold1 = Threshold(registrationName='Threshold1', Input=output_file_object_view_0)
threshold1.Scalars = ['CELLS', 'Volume']
threshold1.LowerThreshold = 8000.0
threshold1.UpperThreshold = 591572.0

# ----------------------------------------------------------------
# setup the visualization in view 'lineChartView1'
# ----------------------------------------------------------------

# show data from plotGlobalVariablesOverTime1
plotGlobalVariablesOverTime1Display = Show(plotGlobalVariablesOverTime1, lineChartView1, 'XYChartRepresentation')

# trace defaults for the display properties.
plotGlobalVariablesOverTime1Display.AttributeType = 'Row Data'
plotGlobalVariablesOverTime1Display.UseIndexForXAxis = 0
plotGlobalVariablesOverTime1Display.XArrayName = 'Time'
plotGlobalVariablesOverTime1Display.SeriesVisibility = ['maximum_work']
plotGlobalVariablesOverTime1Display.SeriesLabel = ['load_imbalance', 'load_imbalance', 'load_variance', 'load_variance', 'maximum_largest_directed_volume', 'maximum_largest_directed_volume', 'maximum_load', 'maximum_load', 'maximum_work', 'maximum_work', 'minimum_load', 'minimum_load', 'minimum_work', 'minimum_work', 'number_of_communication_edges', 'number_of_communication_edges', 'Time', 'Time', 'total_largest_directed_volume', 'total_largest_directed_volume', 'total_work', 'total_work', 'work_variance', 'work_variance']
plotGlobalVariablesOverTime1Display.SeriesColor = ['load_imbalance', '0', '0', '0', 'load_variance', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'maximum_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'maximum_load', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'maximum_work', '0.6', '0.3100022888532845', '0.6399938963912413', 'minimum_load', '1', '0.5000076295109483', '0', 'minimum_work', '0.6500038147554742', '0.3400015259021897', '0.16000610360875867', 'number_of_communication_edges', '0', '0', '0', 'Time', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'total_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'total_work', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'work_variance', '0.6', '0.3100022888532845', '0.6399938963912413']
plotGlobalVariablesOverTime1Display.SeriesPlotCorner = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display.SeriesLabelPrefix = ''
plotGlobalVariablesOverTime1Display.SeriesLineStyle = ['Time', '1', 'load_imbalance', '1', 'load_variance', '1', 'maximum_largest_directed_volume', '1', 'maximum_load', '1', 'maximum_work', '1', 'minimum_load', '1', 'minimum_work', '1', 'number_of_communication_edges', '1', 'total_largest_directed_volume', '1', 'total_work', '1', 'work_variance', '1']
plotGlobalVariablesOverTime1Display.SeriesLineThickness = ['Time', '2', 'load_imbalance', '2', 'load_variance', '2', 'maximum_largest_directed_volume', '2', 'maximum_load', '2', 'maximum_work', '2', 'minimum_load', '2', 'minimum_work', '2', 'number_of_communication_edges', '2', 'total_largest_directed_volume', '2', 'total_work', '2', 'work_variance', '2']
plotGlobalVariablesOverTime1Display.SeriesMarkerStyle = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display.SeriesMarkerSize = ['Time', '4', 'load_imbalance', '4', 'load_variance', '4', 'maximum_largest_directed_volume', '4', 'maximum_load', '4', 'maximum_work', '4', 'minimum_load', '4', 'minimum_work', '4', 'number_of_communication_edges', '4', 'total_largest_directed_volume', '4', 'total_work', '4', 'work_variance', '4']

# ----------------------------------------------------------------
# setup the visualization in view 'lineChartView2'
# ----------------------------------------------------------------

# show data from plotGlobalVariablesOverTime1
plotGlobalVariablesOverTime1Display_1 = Show(plotGlobalVariablesOverTime1, lineChartView2, 'XYChartRepresentation')

# trace defaults for the display properties.
plotGlobalVariablesOverTime1Display_1.AttributeType = 'Row Data'
plotGlobalVariablesOverTime1Display_1.UseIndexForXAxis = 0
plotGlobalVariablesOverTime1Display_1.XArrayName = 'Time'
plotGlobalVariablesOverTime1Display_1.SeriesVisibility = ['load_imbalance']
plotGlobalVariablesOverTime1Display_1.SeriesLabel = ['load_imbalance', 'load_imbalance', 'load_variance', 'load_variance', 'maximum_largest_directed_volume', 'maximum_largest_directed_volume', 'maximum_load', 'maximum_load', 'maximum_work', 'maximum_work', 'minimum_load', 'minimum_load', 'minimum_work', 'minimum_work', 'number_of_communication_edges', 'number_of_communication_edges', 'Time', 'Time', 'total_largest_directed_volume', 'total_largest_directed_volume', 'total_work', 'total_work', 'work_variance', 'work_variance']
plotGlobalVariablesOverTime1Display_1.SeriesColor = ['load_imbalance', '0', '0', '0', 'load_variance', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'maximum_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'maximum_load', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'maximum_work', '0.6', '0.3100022888532845', '0.6399938963912413', 'minimum_load', '1', '0.5000076295109483', '0', 'minimum_work', '0.6500038147554742', '0.3400015259021897', '0.16000610360875867', 'number_of_communication_edges', '0', '0', '0', 'Time', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'total_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'total_work', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'work_variance', '0.6', '0.3100022888532845', '0.6399938963912413']
plotGlobalVariablesOverTime1Display_1.SeriesPlotCorner = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display_1.SeriesLabelPrefix = ''
plotGlobalVariablesOverTime1Display_1.SeriesLineStyle = ['Time', '1', 'load_imbalance', '1', 'load_variance', '1', 'maximum_largest_directed_volume', '1', 'maximum_load', '1', 'maximum_work', '1', 'minimum_load', '1', 'minimum_work', '1', 'number_of_communication_edges', '1', 'total_largest_directed_volume', '1', 'total_work', '1', 'work_variance', '1']
plotGlobalVariablesOverTime1Display_1.SeriesLineThickness = ['Time', '2', 'load_imbalance', '2', 'load_variance', '2', 'maximum_largest_directed_volume', '2', 'maximum_load', '2', 'maximum_work', '2', 'minimum_load', '2', 'minimum_work', '2', 'number_of_communication_edges', '2', 'total_largest_directed_volume', '2', 'total_work', '2', 'work_variance', '2']
plotGlobalVariablesOverTime1Display_1.SeriesMarkerStyle = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display_1.SeriesMarkerSize = ['Time', '4', 'load_imbalance', '4', 'load_variance', '4', 'maximum_largest_directed_volume', '4', 'maximum_load', '4', 'maximum_work', '4', 'minimum_load', '4', 'minimum_work', '4', 'number_of_communication_edges', '4', 'total_largest_directed_volume', '4', 'total_work', '4', 'work_variance', '4']

# ----------------------------------------------------------------
# setup the visualization in view 'lineChartView3'
# ----------------------------------------------------------------

# show data from plotGlobalVariablesOverTime1
plotGlobalVariablesOverTime1Display_2 = Show(plotGlobalVariablesOverTime1, lineChartView3, 'XYChartRepresentation')

# trace defaults for the display properties.
plotGlobalVariablesOverTime1Display_2.AttributeType = 'Row Data'
plotGlobalVariablesOverTime1Display_2.UseIndexForXAxis = 0
plotGlobalVariablesOverTime1Display_2.XArrayName = 'Time'
plotGlobalVariablesOverTime1Display_2.SeriesVisibility = ['total_work']
plotGlobalVariablesOverTime1Display_2.SeriesLabel = ['load_imbalance', 'load_imbalance', 'load_variance', 'load_variance', 'maximum_largest_directed_volume', 'maximum_largest_directed_volume', 'maximum_load', 'maximum_load', 'maximum_work', 'maximum_work', 'minimum_load', 'minimum_load', 'minimum_work', 'minimum_work', 'number_of_communication_edges', 'number_of_communication_edges', 'Time', 'Time', 'total_largest_directed_volume', 'total_largest_directed_volume', 'total_work', 'total_work', 'work_variance', 'work_variance']
plotGlobalVariablesOverTime1Display_2.SeriesColor = ['load_imbalance', '0', '0', '0', 'load_variance', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'maximum_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'maximum_load', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'maximum_work', '0.6', '0.3100022888532845', '0.6399938963912413', 'minimum_load', '1', '0.5000076295109483', '0', 'minimum_work', '0.6500038147554742', '0.3400015259021897', '0.16000610360875867', 'number_of_communication_edges', '0', '0', '0', 'Time', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'total_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'total_work', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'work_variance', '0.6', '0.3100022888532845', '0.6399938963912413']
plotGlobalVariablesOverTime1Display_2.SeriesPlotCorner = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display_2.SeriesLabelPrefix = ''
plotGlobalVariablesOverTime1Display_2.SeriesLineStyle = ['Time', '1', 'load_imbalance', '1', 'load_variance', '1', 'maximum_largest_directed_volume', '1', 'maximum_load', '1', 'maximum_work', '1', 'minimum_load', '1', 'minimum_work', '1', 'number_of_communication_edges', '1', 'total_largest_directed_volume', '1', 'total_work', '1', 'work_variance', '1']
plotGlobalVariablesOverTime1Display_2.SeriesLineThickness = ['Time', '2', 'load_imbalance', '2', 'load_variance', '2', 'maximum_largest_directed_volume', '2', 'maximum_load', '2', 'maximum_work', '2', 'minimum_load', '2', 'minimum_work', '2', 'number_of_communication_edges', '2', 'total_largest_directed_volume', '2', 'total_work', '2', 'work_variance', '2']
plotGlobalVariablesOverTime1Display_2.SeriesMarkerStyle = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display_2.SeriesMarkerSize = ['Time', '4', 'load_imbalance', '4', 'load_variance', '4', 'maximum_largest_directed_volume', '4', 'maximum_load', '4', 'maximum_work', '4', 'minimum_load', '4', 'minimum_work', '4', 'number_of_communication_edges', '4', 'total_largest_directed_volume', '4', 'total_work', '4', 'work_variance', '4']

# ----------------------------------------------------------------
# setup the visualization in view 'lineChartView4'
# ----------------------------------------------------------------

# show data from plotGlobalVariablesOverTime1
plotGlobalVariablesOverTime1Display_3 = Show(plotGlobalVariablesOverTime1, lineChartView4, 'XYChartRepresentation')

# trace defaults for the display properties.
plotGlobalVariablesOverTime1Display_3.AttributeType = 'Row Data'
plotGlobalVariablesOverTime1Display_3.UseIndexForXAxis = 0
plotGlobalVariablesOverTime1Display_3.XArrayName = 'Time'
plotGlobalVariablesOverTime1Display_3.SeriesVisibility = ['maximum_largest_directed_volume']
plotGlobalVariablesOverTime1Display_3.SeriesLabel = ['load_imbalance', 'load_imbalance', 'load_variance', 'load_variance', 'maximum_largest_directed_volume', 'maximum_largest_directed_volume', 'maximum_load', 'maximum_load', 'maximum_work', 'maximum_work', 'minimum_load', 'minimum_load', 'minimum_work', 'minimum_work', 'number_of_communication_edges', 'number_of_communication_edges', 'Time', 'Time', 'total_largest_directed_volume', 'total_largest_directed_volume', 'total_work', 'total_work', 'work_variance', 'work_variance']
plotGlobalVariablesOverTime1Display_3.SeriesColor = ['load_imbalance', '0', '0', '0', 'load_variance', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'maximum_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'maximum_load', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'maximum_work', '0.6', '0.3100022888532845', '0.6399938963912413', 'minimum_load', '1', '0.5000076295109483', '0', 'minimum_work', '0.6500038147554742', '0.3400015259021897', '0.16000610360875867', 'number_of_communication_edges', '0', '0', '0', 'Time', '0.8899977111467154', '0.10000762951094835', '0.1100022888532845', 'total_largest_directed_volume', '0.220004577706569', '0.4899977111467155', '0.7199969481956207', 'total_work', '0.30000762951094834', '0.6899977111467155', '0.2899977111467155', 'work_variance', '0.6', '0.3100022888532845', '0.6399938963912413']
plotGlobalVariablesOverTime1Display_3.SeriesPlotCorner = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display_3.SeriesLabelPrefix = ''
plotGlobalVariablesOverTime1Display_3.SeriesLineStyle = ['Time', '1', 'load_imbalance', '1', 'load_variance', '1', 'maximum_largest_directed_volume', '1', 'maximum_load', '1', 'maximum_work', '1', 'minimum_load', '1', 'minimum_work', '1', 'number_of_communication_edges', '1', 'total_largest_directed_volume', '1', 'total_work', '1', 'work_variance', '1']
plotGlobalVariablesOverTime1Display_3.SeriesLineThickness = ['Time', '2', 'load_imbalance', '2', 'load_variance', '2', 'maximum_largest_directed_volume', '2', 'maximum_load', '2', 'maximum_work', '2', 'minimum_load', '2', 'minimum_work', '2', 'number_of_communication_edges', '2', 'total_largest_directed_volume', '2', 'total_work', '2', 'work_variance', '2']
plotGlobalVariablesOverTime1Display_3.SeriesMarkerStyle = ['Time', '0', 'load_imbalance', '0', 'load_variance', '0', 'maximum_largest_directed_volume', '0', 'maximum_load', '0', 'maximum_work', '0', 'minimum_load', '0', 'minimum_work', '0', 'number_of_communication_edges', '0', 'total_largest_directed_volume', '0', 'total_work', '0', 'work_variance', '0']
plotGlobalVariablesOverTime1Display_3.SeriesMarkerSize = ['Time', '4', 'load_imbalance', '4', 'load_variance', '4', 'maximum_largest_directed_volume', '4', 'maximum_load', '4', 'maximum_work', '4', 'minimum_load', '4', 'minimum_work', '4', 'number_of_communication_edges', '4', 'total_largest_directed_volume', '4', 'total_work', '4', 'work_variance', '4']

# ----------------------------------------------------------------
# setup the visualization in view 'renderView1'
# ----------------------------------------------------------------

# show data from glyph1
glyph1Display = Show(glyph1, renderView1, 'GeometryRepresentation')

# get color transfer function/color map for 'work'
workLUT = GetColorTransferFunction('work')
workLUT.AutomaticRescaleRangeMode = 'Never'
workLUT.RGBPoints = [0.01876189599921769, 0.0, 1.0, 1.0, 0.06153496929974817, 0.0, 0.0, 1.0, 0.06628753299980711, 0.0, 0.0, 0.501960784314, 0.07104009669986606, 1.0, 0.0, 0.0, 0.11381317000039654, 1.0, 1.0, 0.0]
workLUT.ColorSpace = 'RGB'
workLUT.ScalarRangeInitialized = 1.0

# trace defaults for the display properties.
glyph1Display.Representation = 'Surface'
glyph1Display.ColorArrayName = ['POINTS', 'work']
glyph1Display.LookupTable = workLUT
glyph1Display.Opacity = 0.4
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

# show data from glyph2
glyph2Display = Show(glyph2, renderView1, 'GeometryRepresentation')

# get color transfer function/color map for 'Time'
timeLUT = GetColorTransferFunction('Time')
timeLUT.AutomaticRescaleRangeMode = 'Never'
timeLUT.RGBPoints = [0.0, 0.23137254902, 0.298039215686, 0.752941176471, 0.007728504500036593, 0.865, 0.865, 0.865, 0.015457009000073185, 0.705882352941, 0.0156862745098, 0.149019607843]
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

# show data from threshold1
threshold1Display = Show(threshold1, renderView1, 'UnstructuredGridRepresentation')

# get color transfer function/color map for 'Volume'
volumeLUT = GetColorTransferFunction('Volume')
volumeLUT.AutomaticRescaleRangeMode = 'Never'
volumeLUT.RGBPoints = [0.0, 1.0, 1.0, 1.0, 591572.0, 0.0, 0.0, 0.0]
volumeLUT.ColorSpace = 'RGB'
volumeLUT.NanColor = [1.0, 0.0, 0.0]
volumeLUT.NanOpacity = 0.0
volumeLUT.ScalarRangeInitialized = 1.0

# get opacity transfer function/opacity map for 'Volume'
volumePWF = GetOpacityTransferFunction('Volume')
volumePWF.Points = [0.0, 0.0, 0.5, 0.0, 591572.0, 1.0, 0.5, 0.0]
volumePWF.ScalarRangeInitialized = 1

# trace defaults for the display properties.
threshold1Display.Representation = 'Surface'
threshold1Display.ColorArrayName = ['CELLS', 'Volume']
threshold1Display.LookupTable = volumeLUT
threshold1Display.Opacity = 0.8
threshold1Display.LineWidth = 5.0
threshold1Display.SelectTCoordArray = 'None'
threshold1Display.SelectNormalArray = 'None'
threshold1Display.SelectTangentArray = 'None'
threshold1Display.OSPRayScaleArray = 'Time'
threshold1Display.OSPRayScaleFunction = 'PiecewiseFunction'
threshold1Display.SelectOrientationVectors = 'None'
threshold1Display.ScaleFactor = 0.7673149734735489
threshold1Display.SelectScaleArray = 'Time'
threshold1Display.GlyphType = 'Arrow'
threshold1Display.GlyphTableIndexArray = 'Time'
threshold1Display.GaussianRadius = 0.038365748673677445
threshold1Display.SetScaleArray = ['POINTS', 'Time']
threshold1Display.ScaleTransferFunction = 'PiecewiseFunction'
threshold1Display.OpacityArray = ['POINTS', 'Time']
threshold1Display.OpacityTransferFunction = 'PiecewiseFunction'
threshold1Display.DataAxesGrid = 'GridAxesRepresentation'
threshold1Display.PolarAxes = 'PolarAxesRepresentation'
threshold1Display.ScalarOpacityFunction = volumePWF
threshold1Display.ScalarOpacityUnitDistance = 1.6492728367517786
threshold1Display.OpacityArrayName = ['POINTS', 'Time']

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
threshold1Display.ScaleTransferFunction.Points = [0.0017530030001466912, 0.0, 0.5, 0.0, 0.015457009000073185, 1.0, 0.5, 0.0]

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
threshold1Display.OpacityTransferFunction.Points = [0.0017530030001466912, 0.0, 0.5, 0.0, 0.015457009000073185, 1.0, 0.5, 0.0]

# setup the color legend parameters for each legend in this view

# get color legend/bar for workLUT in view renderView1
workLUTColorBar = GetScalarBar(workLUT, renderView1)
workLUTColorBar.Orientation = 'Horizontal'
workLUTColorBar.WindowLocation = 'Any Location'
workLUTColorBar.Position = [0.2202914798206278, 0.8755340214017071]
workLUTColorBar.Title = 'Rank work'
workLUTColorBar.ComponentTitle = ''
workLUTColorBar.LabelFontSize = 14
workLUTColorBar.AutomaticLabelFormat = 0
workLUTColorBar.LabelFormat = '%-#6.2g'
workLUTColorBar.UseCustomLabels = 1
workLUTColorBar.CustomLabels = [7.0, 14.0, 21.0]
workLUTColorBar.RangeLabelFormat = '%-#6.2g'
workLUTColorBar.ScalarBarLength = 0.4999999999999999

# set color bar visibility
workLUTColorBar.Visibility = 1

# get color legend/bar for timeLUT in view renderView1
timeLUTColorBar = GetScalarBar(timeLUT, renderView1)
timeLUTColorBar.Orientation = 'Horizontal'
timeLUTColorBar.WindowLocation = 'Any Location'
timeLUTColorBar.Position = [0.5341928251121075, 0.03170886075949381]
timeLUTColorBar.Title = 'Object Time'
timeLUTColorBar.ComponentTitle = ''
timeLUTColorBar.LabelFontSize = 14
timeLUTColorBar.AutomaticLabelFormat = 0
timeLUTColorBar.LabelFormat = '%-#6.1g'
timeLUTColorBar.DrawTickLabels = 0
timeLUTColorBar.CustomLabels = [0.0001, 0.001, 0.01]
timeLUTColorBar.RangeLabelFormat = '%-#6.1g'
timeLUTColorBar.ScalarBarLength = 0.33000000000000007

# set color bar visibility
timeLUTColorBar.Visibility = 1

# get color legend/bar for volumeLUT in view renderView1
volumeLUTColorBar = GetScalarBar(volumeLUT, renderView1)
volumeLUTColorBar.Orientation = 'Horizontal'
volumeLUTColorBar.WindowLocation = 'Any Location'
volumeLUTColorBar.Position = [0.09865470852017968, 0.03164556962025313]
volumeLUTColorBar.Title = 'Inter-object volume'
volumeLUTColorBar.ComponentTitle = ''
volumeLUTColorBar.LabelFontSize = 14
volumeLUTColorBar.AutomaticLabelFormat = 0
volumeLUTColorBar.UseCustomLabels = 1
volumeLUTColorBar.CustomLabels = [300000.0]
volumeLUTColorBar.RangeLabelFormat = '%-#6.3g'
volumeLUTColorBar.ScalarBarLength = 0.3299999999999994

# set color bar visibility
volumeLUTColorBar.Visibility = 1

# show color legend
glyph1Display.SetScalarBarVisibility(renderView1, True)

# show color legend
glyph2Display.SetScalarBarVisibility(renderView1, True)

# show color legend
threshold1Display.SetScalarBarVisibility(renderView1, True)

# ----------------------------------------------------------------
# setup color maps and opacity mapes used in the visualization
# note: the Get..() functions create a new object, if needed
# ----------------------------------------------------------------

# get opacity transfer function/opacity map for 'Time'
timePWF = GetOpacityTransferFunction('Time')
timePWF.Points = [0.0, 0.0, 0.5, 0.0, 0.015457009000073185, 1.0, 0.5, 0.0]
timePWF.ScalarRangeInitialized = 1

# get opacity transfer function/opacity map for 'work'
workPWF = GetOpacityTransferFunction('work')
workPWF.Points = [0.01876189599921769, 0.0, 0.5, 0.0, 0.11381317000039654, 1.0, 0.5, 0.0]
workPWF.ScalarRangeInitialized = 1

# ----------------------------------------------------------------
# restore active source
SetActiveSource(plotGlobalVariablesOverTime1)
# ----------------------------------------------------------------


if __name__ == '__main__':
    # generate extracts
    SaveExtracts(ExtractsOutputDirectory='extracts')