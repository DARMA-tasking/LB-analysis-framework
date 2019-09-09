#
#@HEADER
###############################################################################
#
#                              MoveCountsViewer.py
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
# This script was written by Philippe P. Pebay, NexGen Analytics LC 2019
# Please do not redistribute without permission

# Import relevant modules
import csv
import vtk

# Number of processors
n_p = 8

# Create storage for vertex values
vertex_name = "Node ID"
vertex_data = vtk.vtkIntArray()
vertex_data.SetName(vertex_name)

# Create a directed graph with one vertex per processor and two sets of edges
graph = vtk.vtkMutableDirectedGraph()
graph.GetVertexData().AddArray(vertex_data)
graph.GetVertexData().SetActiveScalars(vertex_name)

# Populate graph vertices
for i in range(n_p):
    vertex_data.InsertNextValue(i)
    graph.AddVertex()

# Compute directed move counts
directed_moves = {}
directed_sizes = {}
for i in range(n_p):
    # Iterate over all files
    file_name = "NodeGossiper-n8-lstats-i5-k4-f4-t1_0.0.{}.vom".format(i)
    with open(file_name, 'r') as f:
        # Instantiate CSV reader
        reader = csv.reader(f, delimiter=',')

        # Iterate over rows of processor file
        for row in reader:
            # Retrieve source node ID
            src_id = int(row[0])
            src_sz = float(row[2])

            # Add edge when source != destination
            if src_id != i:
                directed_moves[(src_id, i)] = directed_moves.get((src_id, i), 0) + 1

# Compute undirected move counts
undirected_moves = {
    (i, j): directed_moves.get((i, j), 0) + directed_moves.get((j, i), 0)
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
    undirected_moves_edge.InsertNextValue(undirected_moves.get((k_s, k_d)))

# Create renderer
renderer = vtk.vtkRenderer()
renderer.SetBackground(1, 1, 1)
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
        gtg.SetScreenSize(50)
        gtg.FilledOn()
    glyphs.append(gtg)

# Square vertex mapper and actor
mapper_vertices = vtk.vtkPolyDataMapper()
mapper_vertices.SetInputConnection(glyphs[1].GetOutputPort())
mapper_vertices.ScalarVisibilityOff()
actor_vertices = vtk.vtkActor()
actor_vertices.SetMapper(mapper_vertices)
actor_vertices.GetProperty().SetColor(0, 0, 0)
actor_vertices.GetProperty().SetOpacity(.3)
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
l_props.SetColor(0,0,0)
l_props.SetFontSize(16)
l_props.BoldOn()
l_props.ItalicOff()
renderer.AddViewProp(actor_labels)

# Create directed edge layout
layout_directed_edges = vtk.vtkEdgeLayout()
layout_directed_edges.SetInputConnection(layout_vertices.GetOutputPort())
layout_directed_edges.SetLayoutStrategy(vtk.vtkPassThroughEdgeStrategy())

# Directed graph to edge lines
directed_edges = vtk.vtkGraphToPolyData()
directed_edges.SetInputConnection(layout_directed_edges.GetOutputPort())
directed_edges.EdgeGlyphOutputOn()
directed_edges.SetEdgeGlyphPosition(.5)

# Arrow source and glyph
arrow_source = vtk.vtkGlyphSource2D()
arrow_source.SetGlyphTypeToEdgeArrow()
arrow_source.SetScale(.075)
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
layout_undirected_edges.SetInputConnection(layout_vertices.GetOutputPort())
layout_undirected_edges.SetLayoutStrategy(vtk.vtkPassThroughEdgeStrategy())

# Undirected graph to edge lines
undirected_edges = vtk.vtkGraphToPolyData()
undirected_edges.SetInputConnection(layout_undirected_edges.GetOutputPort())

# NB: This is a workaround for a bug in VTK7, cf. below
undirected_edges.Update()
undirected_edges.GetOutput().GetCellData().SetActiveScalars(undirected_moves_name)

# Undirected edge mapper and actor
mapper_edges = vtk.vtkPolyDataMapper()
mapper_edges.SetInputConnection(undirected_edges.GetOutputPort())
mapper_edges.SetScalarRange(move_range)
mapper_edges.SetColorModeToMapScalars()
mapper_edges.SetScalarModeToUseCellData()
# The line below should be used in the absence of the VTK7 bug
#mapper_edges.SetArrayName(undirected_moves_name)
mapper_edges.SelectColorArray(undirected_moves_name)
actor_edges = vtk.vtkActor()
actor_edges.SetMapper(mapper_edges)
actor_edges.GetProperty().SetOpacity(.5)
actor_edges.GetProperty().SetLineWidth(2)
renderer.AddViewProp(actor_edges)

# Scalar bar actor
actor_bar = vtk.vtkScalarBarActor()
actor_bar.SetLookupTable(mapper_edges.GetLookupTable())
actor_bar.SetTitle("Object Moves")
actor_bar.SetOrientationToHorizontal()
actor_bar.SetNumberOfLabels(2)
actor_bar.SetWidth(.2)
actor_bar.SetHeight(.08)
actor_bar.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
actor_bar.GetPositionCoordinate().SetValue(.4, .91)
actor_bar.GetTitleTextProperty().SetColor(0., 0., 0.)
actor_bar.GetLabelTextProperty().SetColor(0., 0., 0.)
actor_bar.SetLabelFormat("%g")
renderer.AddViewProp(actor_bar)

# Render window
window = vtk.vtkRenderWindow()
window.AddRenderer(renderer)
window.SetSize(600, 600)
window.SetAlphaBitPlanes(True)
window.SetMultiSamples(0)

# Render and interact
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(window)
window.Render()
interactor.Start()

