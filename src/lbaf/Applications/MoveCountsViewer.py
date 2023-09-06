import os
import sys
import csv
import importlib
import vtk

# pylint:disable=C0413:wrong-import-position
# Use lbaf module from source if lbaf package is not installed
if importlib.util.find_spec('lbaf') is None:
    sys.path.insert(0, f"{os.sep}".join(os.path.abspath(__file__).split(os.sep)[:-3]))
from lbaf import PROJECT_PATH
from lbaf.Utils.lbsLogging import get_logger, Logger
from lbaf.Utils.lbsArgumentParser import PromptArgumentParser
# pylint:enable=C0413:wrong-import-position

class MoveCountsViewerParameters:
    """A class to describe MoveCountsViewer parameters."""

    def __init__(self, interactive):
        # Set renderer parameters
        self.renderer_background = [1, 1, 1]

        # Set actor_vertices parameters
        self.actor_vertices_screen_size = 50 if interactive else 5000
        self.actor_vertices_color = [0, 0, 0]
        self.actor_vertices_opacity = .3 if interactive else .5

        # Set actor_labels parameters
        self.actor_labels_color = [0, 0, 0]
        self.actor_labels_font_size = 16 if interactive else 150
        self.actor_edges_opacity = .5 if interactive else 1
        self.actor_edges_line_width = 2 if interactive else 15

        # Set actor_arrows parameters
        self.actor_arrows_edge_glyph_position = .5
        self.actor_arrows_source_scale = .075

        # Set actor_bar parameters
        self.actor_bar_number_of_labels = 2
        self.actor_bar_width = .2
        self.actor_bar_heigth = .08
        self.actor_bar_position = [.4, .91]
        self.actor_bar_title_color = [0, 0, 0]
        self.actor_bar_label_color = [0, 0, 0]

        # Set window parameters
        self.window_size_x = 600
        self.window_size_y = 600

        # Set wti (WindowToImageFilter) parameters
        self.wti_scale = 10


class MoveCountsViewer:
    """MoveCountsViewer class"""

    def __init__(self):
        self.__args: dict = None
        self.__logger: Logger = get_logger()

    def __parse_args(self):
        """Parse arguments."""
        parser = PromptArgumentParser(allow_abbrev=False, description="MoveCountsViewer", prompt_default=True)
        parser.add_argument("-p", "--n-processors", help="number of processors", default=8, type=int)
        parser.add_argument("-f", "--input-file-name", help="input file name",
                            default=os.path.join(PROJECT_PATH, "data", "nolb-data", "data"))
        parser.add_argument("-s", "--input-file-suffix", help="input file suffix", default="vom")
        parser.add_argument("-o", "--output-file-name", help="output file name",
                            default=os.path.join(PROJECT_PATH, "output", "move_counts"))
        parser.add_argument("-t", "--output-file-suffix", help="output file suffix", default=8)
        parser.add_argument("-i", "--interactive", type=bool, help="interactive call", default=False)
        self.__args = parser.parse_args()

    def check_args(self) -> bool:
        """Validate input arguments."""
        if self.__args.output_file_name is None:
            self.__args.output_file_name = self.__args.input_file_name
        # If number of processors is not provided or set to 0
        if self.__args.n_processors == 0:
            self.__logger.error("At least one processor needs to be defined. Exiting.")
            return False
        # If  invalid file name is provided
        elif (not self.__args.input_file_name.strip() or self.__args.input_file_name.strip() == "''"):
            self.__logger.error("A file name needs to be defined. Exiting.")
            return False
        return True

    def compute_move_counts_viewer(self):
        """Compute MoveCountsViewer."""

        # Instantiate MoveCountsViewerParameters
        viewer_params = MoveCountsViewerParameters(self.__args.interactive)

        # Create storage for vertex values
        vertex_name = "Node ID"
        vertex_data = vtk.vtkIntArray()
        vertex_data.SetName(vertex_name)

        # Create a directed graph with one vertex per processor
        # and two sets of edges
        graph = vtk.vtkMutableDirectedGraph()
        graph.GetVertexData().AddArray(vertex_data)
        graph.GetVertexData().SetActiveScalars(vertex_name)

        # Populate graph vertices
        for i in range(self.__args.n_processors):
            vertex_data.InsertNextValue(i)
            graph.AddVertex()

        # Compute directed move counts
        directed_moves = {}
        # directed_sizes = {} (unused)
        for i in range(self.__args.n_processors):
            # Iterate over all files
            with open(
                f"{self.__args.input_file_name}.{i}.{self.__args.input_file_suffix}", 'r', encoding="utf-8"
            ) as input_file:
                # Instantiate CSV reader
                reader = csv.reader(input_file, delimiter=",")

                # Iterate over rows of processor file
                for row in reader:
                    # Retrieve source node ID
                    src_id = int(row[0])
                    # src_sz = float(row[2]) (unused)

                    # Add edge when source != destination
                    if src_id != i:
                        directed_moves[(src_id, i)] = directed_moves.get(
                            (src_id, i), 0) + 1
        # Compute undirected move counts
        undirected_moves = {
            (i, j): directed_moves.get((i, j), 0) + directed_moves.get(
                (j, i), 0)
            for (i, j), v in directed_moves.items()}

        # Keep track of extremal values
        move_range = (min(directed_moves.values()),
                      max(undirected_moves.values()))

        # Attach directed moves storage to edges
        directed_moves_name = "Directed Move Counts"
        directed_moves_edge = vtk.vtkIntArray()
        directed_moves_edge.SetName(directed_moves_name)
        graph.GetEdgeData().AddArray(directed_moves_edge)
        graph.GetEdgeData().SetActiveScalars(directed_moves_name)

        # Attach undirected moves storage to edges
        undirected_moves_name = "Undirected Move Counts"
        undirected_moves_edge = vtk.vtkIntArray()
        undirected_moves_edge.SetName(undirected_moves_name)
        graph.GetEdgeData().AddArray(undirected_moves_edge)

        # Populate all edge data
        for (k_s, k_d), v in directed_moves.items():
            graph.AddGraphEdge(k_s, k_d)
            directed_moves_edge.InsertNextValue(v)
            undirected_moves_edge.InsertNextValue(undirected_moves.get(
                (k_s, k_d)))

        # Create renderer
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(viewer_params.renderer_background)
        renderer.GradientBackgroundOff()

        # Create graph vertex layout
        layout_vertices = vtk.vtkGraphLayout()
        layout_vertices.SetInputData(graph)
        layout_vertices.SetLayoutStrategy(vtk.vtkSimple2DLayoutStrategy())

        # Graph to vertex and square glyphs
        local_glyph_types = {
            0: vtk.vtkGraphToGlyphs.VERTEX,
            1: vtk.vtkGraphToGlyphs.SQUARE}
        glyphs = []
        for k, v in local_glyph_types.items():
            gtg = vtk.vtkGraphToGlyphs()
            gtg.SetInputConnection(layout_vertices.GetOutputPort())
            gtg.SetGlyphType(v)
            gtg.SetRenderer(renderer)
            if k:
                gtg.SetScreenSize(viewer_params.actor_vertices_screen_size)
                gtg.FilledOn()
            glyphs.append(gtg)

        # Square vertex mapper and actor
        mapper_vertices = vtk.vtkPolyDataMapper()
        mapper_vertices.SetInputConnection(glyphs[1].GetOutputPort())
        mapper_vertices.ScalarVisibilityOff()
        actor_vertices = vtk.vtkActor()
        actor_vertices.SetMapper(mapper_vertices)
        actor_vertices.GetProperty().SetColor(
            viewer_params.actor_vertices_color)
        actor_vertices.GetProperty().SetOpacity(
            viewer_params.actor_vertices_opacity)
        renderer.AddViewProp(actor_vertices)

        # Vertex labels
        labels = vtk.vtkLabeledDataMapper()
        labels.SetInputConnection(glyphs[0].GetOutputPort())
        labels.SetLabelModeToLabelFieldData()
        labels.SetFieldDataName(vertex_name)
        actor_labels = vtk.vtkActor2D()
        actor_labels.SetMapper(labels)
        l_props = labels.GetLabelTextProperty()
        l_props.SetJustificationToCentered()
        l_props.SetVerticalJustificationToCentered()
        l_props.SetColor(viewer_params.actor_labels_color)
        l_props.SetFontSize(viewer_params.actor_labels_font_size)
        l_props.BoldOn()
        l_props.ItalicOff()
        renderer.AddViewProp(actor_labels)

        # Create directed edge layout
        layout_directed_edges = vtk.vtkEdgeLayout()
        layout_directed_edges.SetInputConnection(
            layout_vertices.GetOutputPort())
        layout_directed_edges.SetLayoutStrategy(
            vtk.vtkPassThroughEdgeStrategy())

        # Directed graph to edge lines
        directed_edges = vtk.vtkGraphToPolyData()
        directed_edges.SetInputConnection(layout_directed_edges.GetOutputPort())
        directed_edges.EdgeGlyphOutputOn()
        directed_edges.SetEdgeGlyphPosition(
            viewer_params.actor_arrows_edge_glyph_position)

        # Arrow source and glyph
        arrow_source = vtk.vtkGlyphSource2D()
        arrow_source.SetGlyphTypeToEdgeArrow()
        arrow_source.SetScale(viewer_params.actor_arrows_source_scale)
        arrow_glyph = vtk.vtkGlyph3D()
        arrow_glyph.SetInputConnection(0, directed_edges.GetOutputPort(1))
        arrow_glyph.SetInputConnection(1, arrow_source.GetOutputPort())
        arrow_glyph.ScalingOff()
        arrow_glyph.SetColorModeToColorByScalar()

        # Arrow mapper and actor
        mapper_arrows = vtk.vtkPolyDataMapper()
        mapper_arrows.SetInputConnection(arrow_glyph.GetOutputPort())
        mapper_arrows.SetScalarRange(move_range)
        actor_arrows = vtk.vtkActor()
        actor_arrows.SetMapper(mapper_arrows)
        renderer.AddViewProp(actor_arrows)

        # Create undirected edge layout
        layout_undirected_edges = vtk.vtkEdgeLayout()
        layout_undirected_edges.SetInputConnection(
            layout_vertices.GetOutputPort())
        layout_undirected_edges.SetLayoutStrategy(
            vtk.vtkPassThroughEdgeStrategy())

        # Undirected graph to edge lines
        undirected_edges = vtk.vtkGraphToPolyData()
        undirected_edges.SetInputConnection(
            layout_undirected_edges.GetOutputPort())

        # NB: This is a workaround for a bug in VTK7, cf. below
        undirected_edges.Update()
        undirected_edges.GetOutput().GetCellData().SetActiveScalars(
            undirected_moves_name)

        # Undirected edge mapper and actor
        mapper_edges = vtk.vtkPolyDataMapper()
        mapper_edges.SetInputConnection(undirected_edges.GetOutputPort())
        mapper_edges.SetScalarRange(move_range)
        mapper_edges.SetColorModeToMapScalars()
        mapper_edges.SetScalarModeToUseCellData()
        # The line below should be used in the absence of the VTK7 bug
        # mapper_edges.SetArrayName(undirected_moves_name)
        mapper_edges.SelectColorArray(undirected_moves_name)
        actor_edges = vtk.vtkActor()
        actor_edges.SetMapper(mapper_edges)
        actor_edges.GetProperty().SetOpacity(
            viewer_params.actor_edges_opacity)
        actor_edges.GetProperty().SetLineWidth(
            viewer_params.actor_edges_line_width)
        renderer.AddViewProp(actor_edges)

        # Reset camera to set it up based on edge actor
        renderer.ResetCamera()

        # Scalar bar actor
        actor_bar = vtk.vtkScalarBarActor()
        actor_bar.SetLookupTable(mapper_edges.GetLookupTable())
        actor_bar.SetTitle("Object Moves")
        actor_bar.SetOrientationToHorizontal()
        actor_bar.SetNumberOfLabels(viewer_params.actor_bar_number_of_labels)
        actor_bar.SetWidth(viewer_params.actor_bar_width)
        actor_bar.SetHeight(viewer_params.actor_bar_heigth)
        actor_bar.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        actor_bar.GetPositionCoordinate().SetValue(
            viewer_params.actor_bar_position[0],
            viewer_params.actor_bar_position[1])
        actor_bar.GetTitleTextProperty().SetColor(
            viewer_params.actor_bar_title_color)
        actor_bar.GetLabelTextProperty().SetColor(
            viewer_params.actor_bar_label_color)
        actor_bar.SetLabelFormat("%g")
        renderer.AddViewProp(actor_bar)

        # Render window
        window = vtk.vtkRenderWindow()
        window.AddRenderer(renderer)
        window.SetSize(viewer_params.window_size_x, viewer_params.window_size_y)
        window.SetAlphaBitPlanes(True)
        window.SetMultiSamples(0)

        # Run interactive MoveCountsViewer if demanded
        if self.__args.interactive:
            # Render and interact
            interactor = vtk.vtkRenderWindowInteractor()
            interactor.SetRenderWindow(window)
            window.Render()
            interactor.Start()

        # Save viewer in output file format otherwise
        else:
            # Window to image
            wti = vtk.vtkWindowToImageFilter()
            window.Render()
            wti.SetInput(window)
            # Set high scale for image quality
            wti.SetScale(viewer_params.wti_scale)
            # Save with alpha channel for transparency
            wti.SetInputBufferTypeToRGBA()

            # Write PNG image
            writer = vtk.vtkPNGWriter()
            writer.SetInputConnection(wti.GetOutputPort())
            writer.SetFileName(
                f"{self.__args.output_file_name}.{self.__args.output_file_suffix}")
            writer.Write()

    def run(self):
        """Run the MoveCountViewer logic."""
        # Parse command line arguments
        self.__parse_args()

        # Print startup information
        svi = sys.version_info
        self.__logger.info(f"### Started with Python {svi.major}.{svi.minor}.{svi.micro}")

        # Parse command line arguments
        self.__parse_args()
        if not self.check_args():
            return 1

        self.__logger.info("# Parsing command line arguments")

        # Execute viewer
        self.compute_move_counts_viewer()
        return 0


if __name__ == "__main__":
    MoveCountsViewer().run()
