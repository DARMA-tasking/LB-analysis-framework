from logging import Logger
import os
import sys
import math
import numbers
import random
import vtk

from .lbsGridStreamer import GridStreamer
from ..Model.lbsPhase import Phase

class MeshBasedVisualizer:
    """A class to visualize LBAF results via mesh files and VTK views."""

    def __init__(
        self,
        logger: Logger,
        phases: list,
        grid_size: list,
        object_jitter=0.0,
        output_dir='.',
        output_file_stem="LBAF_out",
        distributions={},
        statistics ={},
        resolution=1.,
    ):
        """ Class constructor:
            phases: list of Phase instances
            grid_size: iterable containing grid sizes in each dimension
            object_jitter: coefficient of random jitter with magnitude < 1
            f: file name stem
            r: grid_resolution value
            output_dir: output directory
        """
        # Assign logger to instance variable
        self.__logger = logger

        # Make sure that Phase instances were passed
        if not all([isinstance(p, Phase) for p in phases]):
            self.__logger.error(
                "Mesh writer expects a list of Phase instances as input")
            raise SystemExit(1)
        self.__phases = phases

        # Ensure that all phases have the same number of ranks
        n_r = phases[0].get_number_of_ranks()
        if not all([p.get_number_of_ranks() == n_r for p in phases[1:]]):
            self.__logger.error(
                f"All phases must have {n_r} ranks as the first one")
            raise SystemExit(1)
        self.__n_ranks =  n_r
        
        # Ensure that specified grid resolution is correct
        if not isinstance(resolution, numbers.Number) or resolution <= 0.:
            self.__logger.error("Grid resolution must be a positive number")
            raise SystemExit(1)
        self.__grid_resolution = float(resolution)

        # Determine available dimensions for object placement in ranks
        self.__grid_size = grid_size
        self.__rank_dims = [
            d for d in range(3) if self.__grid_size[d] > 1]

        # Compute constant per object jitter
        self.__jitter_dims = {
            i: [(random.random() - 0.5) * object_jitter
                if d in self.__rank_dims
                else 0.0 for d in range(3)]
            for i in self.__phases[0].get_object_ids()}

        # Assemble file and path names from constructor parameters
        self.__rank_file_name = f"{output_file_stem}_rank_view.e"
        self.__object_file_name = f"{output_file_stem}_object_view"
        self.__output_dir = output_dir
        if self.__output_dir is not None:
            self.__rank_file_name = os.path.join(
                self.__output_dir,
                self.__rank_file_name)
            self.__object_file_name = os.path.join(
                self.__output_dir,
                self.__object_file_name)

        # Retrieve and verify rank attribute distributions
        dis_l = distributions.get("load", [])
        dis_w = distributions.get("work", [])
        if not (n_dis := len(dis_l)) == len(dis_w):
            self.__logger.error(
                f"Both load and work distributions must have {n_dis} entries")
            raise SystemExit(1)
        self.__distributions = distributions
        self.__work_range = (
            min(min(dis_w, key=min)), max(max(dis_w, key=max)))

        # Create attribute data arrays for rank loads and works
        self.__loads, self.__works = [], []
        for _ in range(n_dis):
            # Create and append new load and work point arrays
            l_arr, w_arr = vtk.vtkDoubleArray(), vtk.vtkDoubleArray()
            l_arr.SetName("Load")
            w_arr.SetName("Work")
            l_arr.SetNumberOfTuples(self.__n_ranks)
            w_arr.SetNumberOfTuples(self.__n_ranks)
            self.__loads.append(l_arr)
            self.__works.append(w_arr)

        # Iterate over ranks and create rank mesh points
        self.__rank_points = vtk.vtkPoints()
        self.__rank_points.SetNumberOfPoints(self.__n_ranks)
        for i in range(self.__n_ranks):
            # Insert point based on Cartesian coordinates
            self.__rank_points.SetPoint(i, [
                self.__grid_resolution * c
                for c in self.global_id_to_cartesian(
                    i, self.__grid_size)])

            # Set point attributes from distribution values
            for l, (l_arr, w_arr) in enumerate(
                zip(self.__loads, self.__works)):
                l_arr.SetTuple1(i, dis_l[l][i])
                w_arr.SetTuple1(i, dis_w[l][i])

        # Iterate over all possible rank links and create edges
        self.__rank_lines = vtk.vtkCellArray()
        index_to_edge = {}
        edge_index = 0
        for i in range(self.__n_ranks):
            for j in range(i + 1, self.__n_ranks):
                # Insert new link based on endpoint indices
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, j)
                self.__rank_lines.InsertNextCell(line)

                # Update flat index map
                index_to_edge[edge_index] = frozenset([i, j])
                edge_index += 1

        # Number of edges is fixed due to vtkExodusIIWriter limitation
        n_e = int(self.__n_ranks * (self.__n_ranks - 1) / 2)
        self.__logger.info(f"Creating rank mesh with {self.__n_ranks} points and {n_e} edges")

        # Create attribute data arrays for edge sent volumes
        self.__volumes = []
        for i, sent in enumerate(self.__distributions["sent"]):
            # Reduce directed edges into undirected ones
            u_edges = {}
            for k, v in sent.items():
                u_edges[frozenset(k)] = u_edges.setdefault(
                    frozenset(k), 0.) + v

            # Create and append new volume array for edges
            v_arr = vtk.vtkDoubleArray()
            v_arr.SetName("Largest Directed Volume")
            v_arr.SetNumberOfTuples(n_e)
            self.__volumes.append(v_arr)
            
            # Assign edge volume values
            self.__logger.debug(f"\titeration {i} edges:")
            for e, edge in index_to_edge.items():
                v = u_edges.get(edge, float("nan"))
                v_arr.SetTuple1(e, v)
                self.__logger.debug(f"\t{e} {edge}): {v}")

        # Create and populate field arrays for statistics
        self.__field_data = {}
        for stat_name, stat_values in statistics.items():
            # Skip non-list entries
            if not isinstance(stat_values, list):
                continue

            # Create one singleton for each value of each statistic
            for v in stat_values:
                s_arr = vtk.vtkDoubleArray()
                s_arr.SetNumberOfTuples(1)
                s_arr.SetTuple1(0, v)
                s_arr.SetName(stat_name)
                self.__field_data.setdefault(stat_name, []).append(s_arr)


    @staticmethod
    def global_id_to_cartesian(flat_id, grid_sizes):
        """ Map global index to its Cartesian grid coordinates."""
        # Sanity check
        n01 = grid_sizes[0] * grid_sizes[1]
        if flat_id < 0 or flat_id >= n01 * grid_sizes[2]:
            return None, None, None

        # Compute successive Euclidean divisions
        k, r = divmod(flat_id, n01)
        j, i = divmod(r, grid_sizes[0])

        # Return Cartesian coordinates
        return i, j, k

    def create_object_mesh(self, phase: Phase, object_mapping: set):
        """ Map objects to polygonal mesh."""
        # Retrieve number of mesh points and bail out early if empty set
        n_o = phase.get_number_of_objects()
        if not n_o:
            self.__logger.warning("Empty list of objects, cannot write a mesh file")
            return

        # Compute number of communication edges
        n_e = int(n_o * (n_o - 1) / 2)
        self.__logger.info(
            f"Creating object mesh with {n_o} points and {n_e} edges")

        # Create point array for object times
        t_arr = vtk.vtkDoubleArray()
        t_arr.SetName("Time")
        t_arr.SetNumberOfTuples(n_o)

        # Create bit array for object migratability
        b_arr = vtk.vtkBitArray()
        b_arr.SetName("Migratable")
        b_arr.SetNumberOfTuples(n_o)

        # Create and size point set
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(n_o)

        # Iterate over ranks and objects to create mesh points
        ranks = phase.get_ranks()
        point_index, point_to_index, sent_volumes = 0, {}, []
        for rank_id, objects in enumerate(object_mapping):
            # Determine rank offsets
            offsets = [
                self.__grid_resolution * c
                for c in self.global_id_to_cartesian(rank_id, self.__grid_size)]

            # Iterate over objects and create point coordinates
            n_o_rank = len(objects)
            n_o_per_dim = math.ceil(n_o_rank ** (
                1. / len(self.__rank_dims)))
            self.__logger.debug(
                f"Arranging a maximum of {n_o_per_dim} objects per dimension in {self.__rank_dims}")
            o_resolution = self.__grid_resolution / (n_o_per_dim + 1.)
            rank_size = [n_o_per_dim
                         if d in self.__rank_dims
                         else 1 for d in range(3)]
            centering = [0.5 * o_resolution * (n_o_per_dim - 1.)
                         if d in self.__rank_dims
                         else 0.0 for d in range(3)]

            # Order objects of current rank
            r = ranks[rank_id]
            objects_list = sorted(objects, key=lambda x: x.get_id())
            ordered_objects = {o: 0 for o in objects_list if r.is_sentinel(o)}
            for o in objects_list:
                if not r.is_sentinel(o):
                    ordered_objects[o] = 1

            # Add rank objects to points set
            for i, (o, m) in enumerate(ordered_objects.items()):
                # Insert point using offset and rank coordinates
                points.SetPoint(point_index, [
                    offsets[d] - centering[d] + (
                        self.__jitter_dims[o.get_id()][d] + c) * o_resolution
                    for d, c in enumerate(self.global_id_to_cartesian(
                        i, rank_size))])
                t_arr.SetTuple1(point_index, o.get_time())
                b_arr.SetTuple1(point_index, m)

                # Update sent volumes
                for k, v in o.get_sent().items():
                    sent_volumes.append((point_index, k, v))

                # Update maps and counters
                point_to_index[o] = point_index
                point_index += 1

        # Summarize edges
        edges = {
            (tr[0], point_to_index[tr[1]]): tr[2]
            for tr in sent_volumes}

        # Iterate over all possible links and create edges
        lines = vtk.vtkCellArray()
        index_to_edge = {}
        edge_index = 0
        for i in range(n_o):
            for j in range(i + 1, n_o):
                # Insert new link based on endpoint indices
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, j)
                lines.InsertNextCell(line)

                # Update flat index map
                index_to_edge[edge_index] = (i, j)
                edge_index += 1

        # Create and append volume array for edges
        v_arr = vtk.vtkDoubleArray()
        v_arr.SetName("Volume")
        v_arr.SetNumberOfTuples(n_e)

        # Assign edge volume values
        self.__logger.debug(f"\tedges:")
        for e in range(n_e):
            v_arr.SetTuple1(e, edges.get(index_to_edge[e], float("nan")))
            self.__logger.debug(f"\t{e} {index_to_edge[e]}): {v_arr.GetTuple1(e)}")

        # Create and return VTK polygonal data mesh
        pd_mesh = vtk.vtkPolyData()
        pd_mesh.SetPoints(points)
        pd_mesh.GetPointData().SetScalars(t_arr)
        pd_mesh.GetPointData().AddArray(b_arr)
        pd_mesh.SetLines(lines)
        pd_mesh.GetCellData().SetScalars(v_arr)
        return pd_mesh

    def create_color_transfer_function(self, attribute_range, attribute, scheme=None):
        """ Create a color transfer function on scalar attribute."""

        # Create color transfer function
        ctf = vtk.vtkColorTransferFunction()
        ctf.SetNanColor(1., 1., 0.)

        # Set color transfer function depending on chosem scheme
        if scheme == "blue_to_red":
            ctf.SetColorSpaceToDiverging()
            mid_point = (attribute_range[0] + attribute_range[1]) * .5
            ctf.AddRGBPoint(attribute_range[0], .231, .298, .753)
            ctf.AddRGBPoint(mid_point, .865, .865, .865)
            ctf.AddRGBPoint(attribute_range[1], .906, .016, .109)
        elif scheme == "white_to_black":
            ctf.AddRGBPoint(attribute_range[0], 1.0, 1.0, 1.0)
            ctf.AddRGBPoint(attribute_range[1], 0.0, 0.0, 0.0)
        else:
            mid_point = (attribute_range[0] + attribute_range[1]) * .5
            ctf.AddRGBPoint(attribute_range[0], .431, .761, .161)
            ctf.AddRGBPoint(mid_point, .98, .992, .059)
            ctf.AddRGBPoint(attribute_range[1], 1.0, .647, 0.0)

        # Return color transfer function
        return ctf

    def create_scalar_bar_actor(self, mapper, title, width, x, y):
        """ Create scalar bar with default and custome parameters."""

        # Instantiate scalar bar linked to given mapper
        scalar_bar_actor = vtk.vtkScalarBarActor()
        scalar_bar_actor.SetLookupTable(mapper.GetLookupTable())

        # Set default parameters
        scalar_bar_actor.SetOrientationToHorizontal()
        scalar_bar_actor.SetNumberOfLabels(2)
        scalar_bar_actor.SetHeight(0.08)
        scalar_bar_actor.SetLabelFormat("%.3E")
        scalar_bar_actor.SetBarRatio(0.3)
        scalar_bar_actor.DrawTickLabelsOn()
        for text_prop in (
            scalar_bar_actor.GetTitleTextProperty(),
            scalar_bar_actor.GetLabelTextProperty()):
            text_prop.SetColor(0.0, 0.0, 0.0)
            text_prop.ItalicOff()
            text_prop.BoldOff()
            text_prop.SetFontFamilyToArial()

        # Set custom parameters
        scalar_bar_actor.SetTitle(title)
        scalar_bar_actor.SetWidth(width)
        position = scalar_bar_actor.GetPositionCoordinate()
        position.SetCoordinateSystemToNormalizedViewport()
        position.SetValue(x, y, 0.0)

        # Return created scalar bar actor
        return scalar_bar_actor

    def generate(self, gen_meshes, gen_mulmed):
        """ Generate mesh and multimedia outputs."""

        # Write ExodusII rank mesh when requested
        if gen_meshes:
            # Create grid streamer
            streamer = GridStreamer(
                self.__rank_points,
                self.__rank_lines,
                self.__field_data,
                [self.__loads, self.__works],
                self.__volumes,
                lgr=self.__logger)

            # Write to ExodusII file when possible
            if streamer.Error:
                self.__logger.warning(
                    f"Failed to instantiate a grid streamer for file {self.__rank_file_name}")
            else:
                self.__logger.info(
                    f"Writing ExodusII file: {self.__rank_file_name}")
                writer = vtk.vtkExodusIIWriter()
                writer.SetFileName(self.__rank_file_name)
                writer.SetInputConnection(streamer.Algorithm.GetOutputPort())
                writer.WriteAllTimeStepsOn()
                writer.Update()

        # Determine whether phase must be updated
        update_phase = True if len(
            objects := self.__distributions.get("objects", set())
            ) == len(self.__phases) else False

        # Iterate over all object distributions
        phase = self.__phases[0]
        for iteration, object_mapping in enumerate(objects):
            # Update phase when required
            if update_phase:
                phase = self.__phases[iteration]

            # Create object mesh
            object_mesh = self.create_object_mesh(phase, object_mapping)

            # Write to VTP file when requested
            if gen_meshes:
                file_name = f"{self.__object_file_name}_{iteration:02d}.vtp"
                self.__logger.info(f"Writing VTP file: {file_name}")
                writer = vtk.vtkXMLPolyDataWriter()
                writer.SetFileName(file_name)
                writer.SetInputData(object_mesh)
                writer.Update()

            # Generate visualizations when requested
            if gen_mulmed:
                self.__logger.info("Generating visualizations")
                # Create rank mesh for current phase
                rank_mesh = vtk.vtkPolyData()
                rank_mesh.SetPoints(self.__rank_points)
                rank_mesh.SetLines(self.__rank_lines)
                rank_mesh.GetPointData().SetScalars(self.__works[iteration])

                # Create square glyphs at ranks
                square_glyph = vtk.vtkGlyphSource2D()
                square_glyph.SetGlyphTypeToSquare()
                square_glyph.SetScale(.95)
                square_glyph.FilledOn()
                square_glyph.CrossOff()
                rank_glypher = vtk.vtkGlyph2D()
                rank_glypher.SetSourceConnection(square_glyph.GetOutputPort())
                rank_glypher.SetInputData(rank_mesh)
                rank_glypher.SetScaleModeToDataScalingOff()

                # Create color scheme and scalar bar for rank glyphs
                work_ctf = self.create_color_transfer_function(
                    self.__work_range, self.__works[iteration], "blue_to_red")

                # Create mapper and actor for rank mesh
                rank_mapper = vtk.vtkPolyDataMapper()
                rank_mapper.SetInputConnection(rank_glypher.GetOutputPort())
                rank_mapper.SetLookupTable(work_ctf)
                rank_mapper.SetScalarRange(self.__work_range)

                # Create rank work and scalar bar actors
                rank_actor = vtk.vtkActor()
                rank_actor.SetMapper(rank_mapper)
                rank_actor.GetProperty().SetOpacity(0.6)
                work_actor = self.create_scalar_bar_actor(
                    rank_mapper, "Rank Work", 0.6, 0.2, 0.9)

                # Create renderer
                renderer = vtk.vtkRenderer()
                renderer.SetBackground(1.0, 1.0, 1.0)
                renderer.AddActor(rank_actor)
                renderer.AddActor2D(work_actor)

                # Create render window
                render_window = vtk.vtkRenderWindow()
                render_window.SetWindowName("LBAF")
                render_window.AddRenderer(renderer)
                render_window.Render()

                # Convert window to image
                w2if = vtk.vtkWindowToImageFilter()
                w2if.SetInput(render_window)
                w2if.SetScale(2)

                # Output PNG file
                writer = vtk.vtkPNGWriter()
                writer.SetFileName(f"LBAF-{iteration}.png")
                writer.SetInputConnection(w2if.GetOutputPort())
                writer.Write()
