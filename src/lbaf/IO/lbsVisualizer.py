import math
import numbers
import os
import random
import sys
from logging import Logger

import matplotlib.pyplot as plt
import vtk

from ..Model.lbsPhase import Phase
from .lbsGridStreamer import GridStreamer


class Visualizer:
    """A class to visualize LBAF results via mesh files and VTK views."""

    def __init__(
        self,
        logger: Logger,
        qoi_request: list,
        continuous_object_qoi: bool,
        phases: list,
        grid_size: list,
        object_jitter=0.0,
        output_dir='.',
        output_file_stem="LBAF_out",
        distributions=None,
        statistics=None,
        resolution=1.):
        """Class constructor:
            qoi_request: description of rank and object quantities of interest
            continuous_object_qoi: always treat object QOI as continuous or not
            phases: list of Phase instances
            grid_size: iterable containing grid sizes in each dimension
            object_jitter: coefficient of random jitter with magnitude < 1
            output_dir: output directory
            output_file_stem: file name stem
            distributions: a dictionary of per-phase QOI distributions
            statistics: a dictionary of per-phase global statistics
            resolution: grid_resolution value."""

        # Assign logger to instance variable
        self.__logger = logger

        # Useful fields
        self.__rank_points = None
        self.__rank_lines = None
        self.__volumes = None
        self.__field_data = None

        if not distributions:
            distributions = {}

        if not statistics:
            distributions = {}

        # Make sure that rank quantity of interest name was passed
        if not isinstance(qoi_request, list) or (l_req := len(qoi_request)) != 3:
            self.__logger.error(
                f"Visualizer expects 3 quantity of interest parameters and not {l_req}")
            raise SystemExit(1)
        if not (rank_qoi := qoi_request[0]) or not isinstance(rank_qoi, str):
            self.__logger.error(
                "Visualizer expects a non-empty rank quantity of interest name")
            raise SystemExit(1)
        self.__rank_qoi = rank_qoi

        # When rank QOI range was passed make sure it is consistent
        rank_qoi_max = qoi_request[1]
        if rank_qoi_max is not None:
            if not isinstance(rank_qoi_max, float):
                self.__logger.error(
                    f"Inconsistent quantity of interest maximum: {rank_qoi_max}")
                raise SystemExit(1)

        # When object QOI name was passed make sure it is consistent
        req_str = f"Creating visualization for rank {self.__rank_qoi}"
        if (object_qoi := qoi_request[2]) and not isinstance(object_qoi, str):
            self.__logger.error(
                "Optional object quantity of interest name must be a string")
            raise SystemExit(1)
        if object_qoi:
            self.__object_qoi = object_qoi
            req_str += f" and object {self.__object_qoi}"
        else:
            self.__object_qoi = None
        self.__logger.info(req_str)

        # Make sure that Phase instances were passed
        if not all([isinstance(p, Phase) for p in phases.values()]):
            self.__logger.error(
                "Visualizer expects a dictionary of phases as input")
            raise SystemExit(1)
        self.__phases = phases

        # Ensure that all phases have the same number of ranks
        n_r = next(iter(phases.values())).get_number_of_ranks()
        if not all([p.get_number_of_ranks() == n_r for p in phases.values()]):
            self.__logger.error(
                f"All phases must have {n_r} ranks as the first one")
            raise SystemExit(1)
        self.__n_ranks =  n_r

        # Ensure that specified grid resolution is correct
        if not isinstance(resolution, numbers.Number) or resolution <= 0.:
            self.__logger.error(
                "Grid resolution must be a positive number")
            raise SystemExit(1)
        self.__grid_resolution = float(resolution)

        # Determine available dimensions for object placement in ranks
        self.__grid_size = grid_size
        self.__rank_dims = [
            d for d in range(3) if self.__grid_size[d] > 1]
        self.__max_o_per_dim = 0

        # Compute constant per object jitter
        self.__jitter_dims = {
            i: [(random.random() - 0.5) * object_jitter
                if d in self.__rank_dims
                else 0.0 for d in range(3)]
            for i in next(iter(self.__phases.values())).get_object_ids()}

        # Initialize maximum object atrribute values
        self.__object_load_max = 0.0
        self.__object_volume_max = 0.0

        # Compute discrete or pseudo-continuous object QOI range
        self.__object_qoi_range = self.compute_object_qoi_range(
            object_qoi, continuous_object_qoi)

        # Assemble file and path names from constructor parameters
        self.__rank_file_name = f"{output_file_stem}_rank_view.e"
        self.__object_file_name = f"{output_file_stem}_object_view"
        if output_dir is not None:
            self.__rank_file_name = os.path.join(
                output_dir, self.__rank_file_name)
            self.__object_file_name = os.path.join(
                output_dir, self.__object_file_name)
            self.__visualization_file_name = os.path.join(
                output_dir, output_file_stem)

        # Retrieve and verify rank attribute distributions
        self.__rank_attributes = {
            k: distributions.get(f"rank {k}", [])
            for k in list({"load", "work", self.__rank_qoi})}
        if not all((n_dis := len(self.__rank_attributes["load"])) == len(v)
                   for v in self.__rank_attributes.values()):
            self.__logger.error(
                "Rank attribute distributions do not have equal lengths")
            raise SystemExit(1)
        self.__distributions = distributions

        # Retrieve and verify globale statistics
        if not isinstance(statistics, dict):
            self.__logger.error(
                "Global statistics must be passed in a dictionary")
            raise SystemExit(1)
        self.__statistics = statistics

        # Assign or compute rank quantity of interest range
        self.__rank_qoi_range = [
            min(y for x in self.__rank_attributes[self.__rank_qoi] for y in x)]
        if rank_qoi_max is None:
            self.__rank_qoi_range.append(
                max(y for x in self.__rank_attributes[self.__rank_qoi] for y in x))
        else:
            self.__rank_qoi_range.append(rank_qoi_max)
        self.__logger.info(
            f"\trank {self.__rank_qoi} range: [{self.__rank_qoi_range[0]:.4g}; {self.__rank_qoi_range[1]:.4g}]")

        # Create attribute data arrays for rank loads and works
        self.__logger.info(
            "Adding attributes " + ", ".join(self.__rank_attributes))
        self.__qoi_dicts = []
        for _ in range(n_dis):
            # Create and append new rank QOI dictionaries
            arr_dict = {}
            self.__qoi_dicts.append(arr_dict)
            for k in self.__rank_attributes.keys():
                qoi_arr = vtk.vtkDoubleArray()
                qoi_arr.SetName(k)
                qoi_arr.SetNumberOfTuples(self.__n_ranks)
                arr_dict[k] = qoi_arr

    @staticmethod
    def global_id_to_cartesian(flat_id, grid_sizes):
        """Map global index to its Cartesian grid coordinates."""
        # Sanity check
        n01 = grid_sizes[0] * grid_sizes[1]
        if flat_id < 0 or flat_id >= n01 * grid_sizes[2]:
            return None, None, None

        # Compute successive Euclidean divisions
        k, r = divmod(flat_id, n01)
        j, i = divmod(r, grid_sizes[0])

        # Return Cartesian coordinates
        return i, j, k

    def compute_object_qoi_range(self, object_qoi, continuous_object_qoi):
        """Decide object quantity storage type and compute it."""

        # Return empty range if no object QOI was passed
        if not object_qoi:
            return ()

        # Initialize space-time object QOI range attributes
        oq_min, oq_max, oq_all, = math.inf, -math.inf, set()

        # Iterate over all phases
        for phase in self.__phases.values():
            # Iterate over all objects in phase
            for o in phase.get_objects():
                # Update maximum object load as needed
                if (ol := o.get_load()) > self.__object_load_max:
                    self.__object_load_max = ol

                # Retain all QOI values while support remains small
                oq = getattr(o, f"get_{object_qoi}")()

                # Check if the QOI value ends in .0, then convert to integer
                if isinstance(oq, float) and oq.is_integer():
                    oq = int(oq)

                if not continuous_object_qoi:
                    oq_all.add(oq)
                    if len(oq_all) > 20:
                        # Do not store QOI values if support is too large
                        oq_all = None
                        continuous_object_qoi = True

                # Update extrema
                if oq < oq_min:
                    oq_min = oq
                if oq > oq_max:
                    oq_max = oq

        # Store either range or support
        if continuous_object_qoi:
            object_qoi_range = (oq_min, oq_max)
            self.__logger.info(
                f"\tobject {self.__object_qoi} range: [{object_qoi_range[0]:.4g}; {object_qoi_range[1]:.4g}]")
        else:
            object_qoi_range = oq_all
            self.__logger.info(
                f"\tobject {self.__object_qoi} has {len(object_qoi_range)} distinct values")

        # Return cpmputed QOI range
        return object_qoi_range

    def __create_rank_mesh(self, iteration: int):
        """Map ranks to polygonal mesh."""
        # Assemble and return polygonal mesh
        pd_mesh = vtk.vtkPolyData()
        pd_mesh.SetPoints(self.__rank_points)
        pd_mesh.SetLines(self.__rank_lines)
        pd_mesh.GetPointData().SetScalars(
            self.__qoi_dicts[iteration][self.__rank_qoi])
        return pd_mesh

    def __create_object_mesh(self, phase: Phase, object_mapping: set):
        """Map objects to polygonal mesh."""
        # Retrieve number of mesh points and bail out early if empty set
        n_o = phase.get_number_of_objects()
        if not n_o:
            self.__logger.warning("Empty list of objects, cannot write a mesh file")
            return

        # Create point array for object quantity of interest
        q_arr = vtk.vtkDoubleArray()
        q_arr.SetName(self.__object_qoi)
        q_arr.SetNumberOfTuples(n_o)

        # Load array must be added when it is not the object QOI
        if self.__object_qoi != "load":
            l_arr = vtk.vtkDoubleArray()
            l_arr.SetName("load")
            l_arr.SetNumberOfTuples(n_o)
        else:
            l_arr =  None

        # Create bit array for object migratability
        b_arr = vtk.vtkBitArray()
        b_arr.SetName("migratable")
        b_arr.SetNumberOfTuples(n_o)

        # Create and size point set
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(n_o)

        # Retrieve elements constant across all ranks
        p_id = phase.get_id()
        ranks = phase.get_ranks()
        object_qoi = self.__distributions[f"object {self.__object_qoi}"][p_id]

        # Iterate over ranks and objects to create mesh points
        point_index, point_to_index, sent_volumes = 0, {}, []
        for rank_id, objects in enumerate(object_mapping):
            # Determine rank offsets
            offsets = [
                self.__grid_resolution * c
                for c in self.global_id_to_cartesian(
                    rank_id, self.__grid_size)]

            # Compute local object block parameters
            n_o_rank = len(objects)
            n_o_per_dim = math.ceil(n_o_rank ** (
                1. / len(self.__rank_dims)))
            if n_o_per_dim > self.__max_o_per_dim:
                self.__max_o_per_dim = n_o_per_dim
            o_resolution = self.__grid_resolution / (n_o_per_dim + 1.)

            # Iterate over objects and create point coordinates
            self.__logger.debug(
                f"Arranging a maximum of {n_o_per_dim} objects per dimension in {self.__rank_dims}")
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
                        self.__jitter_dims.get(
                            o.get_id(),
                            (0.0, 0.0, 0.0))[d] + c) * o_resolution
                    for d, c in enumerate(self.global_id_to_cartesian(
                        i, rank_size))])

                # Set object attributes
                q_arr.SetTuple1(point_index, object_qoi[o.get_id()])
                b_arr.SetTuple1(point_index, m)
                if l_arr:
                    l_arr.SetTuple1(point_index, o.get_load())

                # Update sent volumes
                for k, v in o.get_sent().items():
                    sent_volumes.append((point_index, k, v))

                # Update maps and counters
                point_to_index[o] = point_index
                point_index += 1

        # Initialize containers for edge lines and attribute
        v_arr = vtk.vtkDoubleArray()
        v_arr.SetName("volume")
        lines = vtk.vtkCellArray()
        n_e, edge_values = 0, {}

        # Create object mesh edges and assign volume values
        self.__logger.debug("\tCreating inter-object communication edges:")
        for pt_index, k, v in sent_volumes:
            # Retrieve undirected edge point indices
            i, j = sorted((pt_index, point_to_index[k]))
            ij = frozenset((i, j))

            # Update or create  edge
            if (e_ij := edge_values.get(ij)) is None:
                # Edge must be created
                self.__logger.debug(f"\tcreating edge {n_e} ({i}--{j}): {v}")
                edge_values[ij] = [n_e, v]
                n_e += 1
                v_arr.InsertNextTuple1(v)
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, j)
                lines.InsertNextCell(line)
            else:
                # Edge already exists and must be updated
                e_ij[1] += v
                self.__logger.debug(f"\tupdating edge {e_ij[0]} ({i}--{j}): {e_ij[1]}")
                v_arr.SetTuple1(e_ij[0], e_ij[1])

        # Create and return VTK polygonal data mesh
        self.__logger.info(
            f"Assembling phase {p_id} object mesh with {n_o} points and {n_e} edges")
        pd_mesh = vtk.vtkPolyData()
        pd_mesh.SetPoints(points)
        pd_mesh.SetLines(lines)
        pd_mesh.GetPointData().SetScalars(q_arr)
        pd_mesh.GetPointData().AddArray(b_arr)
        if l_arr:
            pd_mesh.GetPointData().AddArray(l_arr)
        pd_mesh.GetCellData().SetScalars(v_arr)
        return pd_mesh

    @staticmethod
    def create_color_transfer_function(attribute_range, scheme=None):
        """Create a color transfer function given attribute range."""

        # Create dicretizable color transfer function
        ctf = vtk.vtkDiscretizableColorTransferFunction()
        ctf.SetNanColorRGBA(1., 1., 1., 0.)
        ctf.UseBelowRangeColorOn()
        ctf.UseAboveRangeColorOn()

        # Make discrete when requested
        if isinstance(attribute_range, set):
            ctf.DiscretizeOn()
            n_colors = len(attribute_range)
            ctf.IndexedLookupOn()
            ctf.SetNumberOfIndexedColors(n_colors)
            for i, v in enumerate(sorted(attribute_range)):
                ctf.SetAnnotation(v, f"{v}")
                ctf.SetIndexedColorRGBA(i, plt.cm.get_cmap("tab20")(i))
            ctf.Build()
            return ctf

        # Otherwise set color transfer function depending on chosen scheme
        if scheme == "blue_to_red":
            ctf.SetColorSpaceToDiverging()
            mid_point = (attribute_range[0] + attribute_range[1]) * .5
            ctf.AddRGBPoint(attribute_range[0], .231, .298, .753)
            ctf.AddRGBPoint(mid_point, .865, .865, .865)
            ctf.AddRGBPoint(attribute_range[1], .906, .016, .109)
            ctf.SetBelowRangeColor(0.0, 1.0, 0.0)
            ctf.SetAboveRangeColor(1.0, 0.0, 1.0)
        elif scheme == "white_to_black":
            ctf.AddRGBPoint(attribute_range[0], 1.0, 1.0, 1.0)
            ctf.AddRGBPoint(attribute_range[1], 0.0, 0.0, 0.0)
            ctf.SetBelowRangeColor(0.0, 0.0, 1.0)
            ctf.SetAboveRangeColor(1.0, 0.0, 0.0)
        else:
            # Default color spectrum from green to orange via yellow
            mid_point = (attribute_range[0] + attribute_range[1]) * .5
            ctf.AddRGBPoint(attribute_range[0], .431, .761, .161)
            ctf.AddRGBPoint(mid_point, .98, .992, .059)
            ctf.AddRGBPoint(attribute_range[1], 1.0, .647, 0.0)
            ctf.SetBelowRangeColor(0.8, 0.8, .8)
            ctf.SetAboveRangeColor(1.0, 0.0, 1.0)

        # Return color transfer function
        return ctf

    @staticmethod
    def create_scalar_bar_actor(mapper, title, x, y, values=None):
        """Create scalar bar with default and custom parameters."""

        # Instantiate scalar bar linked to given mapper
        scalar_bar_actor = vtk.vtkScalarBarActor()
        scalar_bar_actor.SetLookupTable(mapper.GetLookupTable())

        # Set default parameters
        scalar_bar_actor.SetOrientationToHorizontal()
        scalar_bar_actor.UnconstrainedFontSizeOn()
        scalar_bar_actor.SetHeight(0.08)
        scalar_bar_actor.SetWidth(0.42)
        scalar_bar_actor.SetBarRatio(0.3)
        scalar_bar_actor.DrawTickLabelsOn()
        scalar_bar_actor.SetLabelFormat("%.2G")
        if values:
            scalar_bar_actor.SetNumberOfLabels(len(values))
            scalar_bar_actor.SetAnnotationLeaderPadding(8)
            scalar_bar_actor.SetTitle(title.title().replace('_', ' ') + '\n')
        else:
            scalar_bar_actor.SetNumberOfLabels(2)
            scalar_bar_actor.SetTitle(title.title().replace('_', ' '))
        for text_prop in (
            scalar_bar_actor.GetTitleTextProperty(),
            scalar_bar_actor.GetLabelTextProperty(),
            scalar_bar_actor.GetAnnotationTextProperty()):
            text_prop.SetColor(0.0, 0.0, 0.0)
            text_prop.ItalicOff()
            text_prop.BoldOff()
            text_prop.SetFontFamilyToArial()
            text_prop.SetFontSize(60)

        # Set custom parameters
        position = scalar_bar_actor.GetPositionCoordinate()
        position.SetCoordinateSystemToNormalizedViewport()
        position.SetValue(x, y, 0.0)

        # Return created scalar bar actor
        return scalar_bar_actor

    def __create_rendering_pipeline(
        self,
        iteration: int,
        p_id: int,
        object_mesh,
        edge_width: int,
        glyph_factor: float,
        win_size: int):
        """Create VTK-based pipeline all the way to render window."""

        # Create rank mesh for current phase
        rank_mesh = self.__create_rank_mesh(iteration)

        # Create renderer with parallel projection
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(1.0, 1.0, 1.0)
        renderer.GetActiveCamera().ParallelProjectionOn()

        # Create square glyphs at ranks
        rank_glyph = vtk.vtkGlyphSource2D()
        rank_glyph.SetGlyphTypeToSquare()
        rank_glyph.SetScale(.95)
        rank_glyph.FilledOn()
        rank_glyph.CrossOff()
        rank_glypher = vtk.vtkGlyph2D()
        rank_glypher.SetSourceConnection(rank_glyph.GetOutputPort())
        rank_glypher.SetInputData(rank_mesh)
        rank_glypher.SetScaleModeToDataScalingOff()

        # Lower glyphs slightly for visibility
        z_lower = vtk.vtkTransform()
        z_lower.Translate(0.0, 0.0, -0.01)
        trans = vtk.vtkTransformPolyDataFilter()
        trans.SetTransform(z_lower)
        trans.SetInputConnection(rank_glypher.GetOutputPort())

        # Create mapper for rank glyphs
        rank_mapper = vtk.vtkPolyDataMapper()
        rank_mapper.SetInputConnection(trans.GetOutputPort())
        rank_mapper.SetLookupTable(
            self.create_color_transfer_function((
                self.__rank_qoi_range[0], self.__rank_qoi_range[1]),"blue_to_red"))
        rank_mapper.SetScalarRange(self.__rank_qoi_range)

        # Create rank QOI and its scalar bar actors
        rank_actor = vtk.vtkActor()
        rank_actor.SetMapper(rank_mapper)
        qoi_actor = self.create_scalar_bar_actor(
            rank_mapper, f"rank {self.__rank_qoi}", 0.5, 0.9)
        qoi_actor.DrawBelowRangeSwatchOn()
        qoi_actor.SetBelowRangeAnnotation('<')
        qoi_actor.DrawAboveRangeSwatchOn()
        qoi_actor.SetAboveRangeAnnotation('>')
        renderer.AddActor(rank_actor)
        renderer.AddActor2D(qoi_actor)

        # Create object pipeline only when requested
        if self.__object_qoi:
            # Create white to black look-up table
            bw_lut = vtk.vtkLookupTable()
            bw_lut.SetTableRange((0.0, self.__object_volume_max))
            bw_lut.SetSaturationRange(0, 0)
            bw_lut.SetHueRange(0, 0)
            bw_lut.SetValueRange(1, 0)
            bw_lut.SetNanColor(1.0, 1.0, 1.0, 0.0)
            bw_lut.Build()

            # Create mapper for inter-object edges
            edge_mapper = vtk.vtkPolyDataMapper()
            edge_mapper.SetInputData(object_mesh)
            edge_mapper.SetScalarModeToUseCellData()
            edge_mapper.SetScalarRange((0.0, self.__object_volume_max))
            edge_mapper.SetLookupTable(bw_lut)

            # Create communication volume and its scalar bar actors
            edge_actor = vtk.vtkActor()
            edge_actor.SetMapper(edge_mapper)
            edge_actor.GetProperty().SetLineWidth(edge_width)
            volume_actor = self.create_scalar_bar_actor(
                edge_mapper, "Inter-Object Volume", 0.04, 0.04)
            renderer.AddActor(edge_actor)
            renderer.AddActor2D(volume_actor)

            # Compute square root of object loads
            sqrtL = vtk.vtkArrayCalculator()
            sqrtL.SetInputData(object_mesh)
            sqrtL.AddScalarArrayName("load")
            sqrtL_str = "sqrt(load)"
            sqrtL.SetFunction(sqrtL_str)
            sqrtL.SetResultArrayName(sqrtL_str)
            sqrtL.Update()
            sqrtL_out = sqrtL.GetOutput()
            sqrtL_out.GetPointData().SetActiveScalars("migratable")

            # Glyph sentinel and migratable objects separately
            glyph_mapper = None
            for k, v in {0.0: "Square", 1.0: "Circle"}.items():
                # Threshold by migratable status
                thresh = vtk.vtkThresholdPoints()
                thresh.SetInputData(sqrtL_out)
                thresh.ThresholdBetween(k, k)
                thresh.Update()
                thresh_out = thresh.GetOutput()
                if not thresh_out.GetNumberOfPoints():
                    continue
                thresh_out.GetPointData().SetActiveScalars(sqrtL_str)

                # Glyph by square root of object quantity of interest
                glyph = vtk.vtkGlyphSource2D()
                getattr(glyph, f"SetGlyphTypeTo{v}")()
                glyph.SetResolution(32)
                glyph.SetScale(1.0)
                glyph.FilledOn()
                glyph.CrossOff()
                glypher = vtk.vtkGlyph3D()
                glypher.SetSourceConnection(glyph.GetOutputPort())
                glypher.SetInputData(thresh_out)
                glypher.SetScaleModeToScaleByScalar()
                glypher.SetScaleFactor(glyph_factor)
                glypher.Update()
                glypher.GetOutput().GetPointData().SetActiveScalars(
                    self.__object_qoi)

                # Raise glyphs slightly for visibility
                z_raise = vtk.vtkTransform()
                z_raise.Translate(0.0, 0.0, 0.01)
                trans = vtk.vtkTransformPolyDataFilter()
                trans.SetTransform(z_raise)
                trans.SetInputData(glypher.GetOutput())

                # Create mapper and actor for glyphs
                glyph_mapper = vtk.vtkPolyDataMapper()
                glyph_mapper.SetInputConnection(trans.GetOutputPort())
                glyph_mapper.SetLookupTable(
                    self.create_color_transfer_function(
                        self.__object_qoi_range))
                if (is_continuous := isinstance(self.__object_qoi_range, tuple)):
                    glyph_mapper.SetScalarRange(self.__object_qoi_range)
                glyph_actor = vtk.vtkActor()
                glyph_actor.SetMapper(glyph_mapper)
                renderer.AddActor(glyph_actor)

            # Create and add unique scalar bar for object QOI when available
            if glyph_mapper:
                load_actor = self.create_scalar_bar_actor(
                    glyph_mapper, f"object {self.__object_qoi}", 0.52, 0.04,
                    None if is_continuous else self.__object_qoi_range)
                renderer.AddActor2D(load_actor)

        # Create text actor to indicate iteration and imbalance
        lb_data = self.__field_data["load imbalance"]
        text_actor = vtk.vtkTextActor()
        text_actor.SetInput(
            f"Phase ID: {p_id}"
            f"   Iteration: {iteration}/{len(lb_data) - 1}\n"
            f"Load Imbalance: {lb_data[iteration].GetTuple1(0):.4g}")
        text_prop = text_actor.GetTextProperty()
        text_prop.SetColor(0.0, 0.0, 0.0)
        text_prop.ItalicOff()
        text_prop.BoldOff()
        text_prop.SetFontFamilyToArial()
        text_prop.SetFontSize(60)
        text_prop.SetLineSpacing(1.5)
        position = text_actor.GetPositionCoordinate()
        position.SetCoordinateSystemToNormalizedViewport()
        position.SetValue(0.04, 0.91, 0.0)
        renderer.AddActor(text_actor)

        # Create and return render window
        renderer.ResetCamera()
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetWindowName("LBAF")
        render_window.SetSize(win_size, win_size)
        return render_window

    def generate(self, save_meshes: bool, gen_vizqoi: bool):
        """Generate mesh and multimedia outputs."""

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
            for j, qoi_dict in enumerate(self.__qoi_dicts):
                for k, v in self.__rank_attributes.items():
                    qoi_dict[k].SetTuple1(i, v[j][i])

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
        self.__logger.debug(
            f"Assembling rank mesh with {self.__n_ranks} points and {n_e} edges")

        # Create attribute data arrays for edge sent volumes
        self.__volumes = []
        for i, sent in enumerate(self.__distributions["sent"]):
            # Reduce directed edges into undirected ones
            u_edges = {}
            for k, v in sent.items():
                u_edges[frozenset(k)] = u_edges.setdefault(frozenset(k), 0.) + v

            # Create and append new volume array for edges
            v_arr = vtk.vtkDoubleArray()
            v_arr.SetName("largest directed volume")
            v_arr.SetNumberOfTuples(n_e)
            self.__volumes.append(v_arr)

            # Assign edge volume values
            self.__logger.debug(f"\titeration {i} edges:")
            for e, edge in index_to_edge.items():
                v = u_edges.get(edge, float("nan"))
                v_arr.SetTuple1(e, v)
                if v > self.__object_volume_max:
                    self.__object_volume_max = v
                self.__logger.debug(f"\t{e} {edge}): {v}")

        # Create and populate field arrays for statistics
        self.__field_data = {}
        for stat_name, stat_values in self.__statistics.items():
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

        # Write ExodusII rank mesh when requested
        if save_meshes:
            if sys.version_info.major == 3 and sys.version_info.minor == 9:
                self.__logger.error(
                    "Cannot save meshes when using Python 3.9 (issue with vtk 9.1.0). "
                    "Please use Python 3.8 (vtk 9.0.1)."
                )
                raise SystemExit(1)

            # Create grid streamer
            streamer = GridStreamer(
                self.__rank_points,
                self.__rank_lines,
                self.__field_data,
                self.__qoi_dicts,
                self.__volumes,
                logger=self.__logger)

            # Write to ExodusII file when possible
            if streamer.error:
                self.__logger.warning(
                    f"Failed to instantiate a grid streamer for file {self.__rank_file_name}")
            else:
                writer = vtk.vtkExodusIIWriter()
                writer.SetFileName(self.__rank_file_name)
                writer.SetInputConnection(streamer.algorithm.GetOutputPort())
                writer.WriteAllTimeStepsOn()
                writer.Update()
                self.__logger.info(
                    f"Wrote ExodusII file: {self.__rank_file_name}")

        # Determine whether phase must be updated
        update_phase = True if len(
            rank_objects := self.__distributions.get("rank objects", set())
            ) == len(self.__phases) else False

        # Iterate over all object distributions
        phase = next(iter(self.__phases.values()))
        phase_it = iter(self.__phases.values())
        for iteration, object_mapping in enumerate(rank_objects):
            # Update phase when required
            if update_phase:
                phase = next(phase_it)

            # Create object mesh when requested
            if self.__object_qoi:
                object_mesh = self.__create_object_mesh(phase, object_mapping)

                # Write to VTP file when requested
                if save_meshes:
                    file_name = f"{self.__object_file_name}_{iteration:02d}.vtp"
                    writer = vtk.vtkXMLPolyDataWriter()
                    writer.SetFileName(file_name)
                    writer.SetInputData(object_mesh)
                    writer.Update()
                    self.__logger.info(f"Wrote VTP file: {file_name}")
            else:
                object_mesh = None

            # Generate visualizations when requested
            if gen_vizqoi:
                if len(self.__rank_dims) > 2:
                    self.__logger.warning(
                        "Visualization generation not yet implemented in 3-D")
                    continue

                # Compute visualization parameters
                self.__logger.info(
                    f"Generating 2-D visualization for iteration {iteration}:")
                ws = 800
                self.__logger.info(
                    f"\tnumber of pixels: {ws}x{ws}")
                if self.__object_qoi:
                    ew = 0.1 * ws / max(self.__grid_size)
                    self.__logger.info(
                        f"\tcommunication edges width: {ew:.2g}")
                    gf = 0.8 * self.__grid_resolution / (
                        (self.__max_o_per_dim + 1)
                        * math.sqrt(self.__object_load_max))
                    self.__logger.info(
                        f"\tobject glyphs scaling: {gf:.2g}")

                # Run visualization pipeline
                render_window = self.__create_rendering_pipeline(
                    iteration,
                    phase.get_id(),
                    object_mesh,
                    edge_width = ew if self.__object_qoi else None,
                    glyph_factor = gf if self.__object_qoi else None,
                    win_size = ws)
                render_window.Render()

                # Convert window to image
                w2i = vtk.vtkWindowToImageFilter()
                w2i.SetInput(render_window)
                w2i.SetScale(3)

                # Output PNG file
                file_name = f"{self.__visualization_file_name}_{iteration:02d}.png"
                writer = vtk.vtkPNGWriter()
                writer.SetInputConnection(w2i.GetOutputPort())
                writer.SetFileName(file_name)
                writer.SetCompressionLevel(2)
                writer.Write()
                self.__logger.info(f"Wrote PNG file: {file_name}")
