from logging import Logger
import os
import sys
import math
import numbers
import random
import vtk

from .lbsGridStreamer import GridStreamer
from ..Model.lbsPhase import Phase

class MeshWriter:
    """A class to write LBAF results to mesh files via VTK layer."""

    def __init__(
        self,
        logger: Logger,
        phases: list,
        grid_size: list,
        object_jitter=0.0,
        output_dir='.',
        output_file_stem="LBAF_out",
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
        if not all([p.get_number_of_ranks == n_r for p in phases[1:]]):
            self.__logger.error(
                f"All phases must have {n_r} ranks as the first one")
            raise SystemExit(1)
        self.__n_ranks =  n_r
        
        # Ensure that specified grid resolution is correct
        if not isinstance(resolution, numbers.Number) or resolution <= 0.:
            self.__logger.error("Grid resolution must be a positive number")
            raise SystemExit(1)
        self.__grid_resolution = float(resolution)

        # Keep track of mesh properties
        self.__grid_size = grid_size
        self.__object_jitter = object_jitter

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

        # Iterate over ranks and create rank mesh points
        self.__rank_points = vtk.vtkPoints()
        self.__rank_points.SetNumberOfPoints(self.__n_ranks)
        for i in range(self.__n_ranks):
            # Insert point based on Cartesian coordinates
            self.__rank_points.SetPoint(i, [
                self.__grid_resolution * c
                for c in self.global_id_to_cartesian(
                    i, self.__grid_size)])

        # Iterate over all possible rank links and create edges
        self.__rank_lines = vtk.vtkCellArray()
        self.__index_to_edge = {}
        edge_index = 0
        for i in range(self.__n_ranks):
            for j in range(i + 1, self.__n_ranks):
                # Insert new link based on endpoint indices
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, j)
                self.__rank_lines.InsertNextCell(line)

                # Update flat index map
                self.__index_to_edge[edge_index] = frozenset([i, j])
                edge_index += 1

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

    def write_rank_view_file(self, distributions: dict):
        """ Map ranks to grid and write ExodusII file."""
        # Number of edges is fixed due to vtkExodusIIWriter limitation
        n_e = int(self.__n_ranks * (self.__n_ranks - 1) / 2)
        self.__logger.info(f"Creating rank view mesh with {self.__n_ranks} points and {n_e} edges")

        # Create attribute data arrays for rank loads and works
        loads, works = [], []
        for _, _ in zip(distributions["load"], distributions["work"]):
            # Create and append new load and work point arrays
            l_arr, w_arr = vtk.vtkDoubleArray(), vtk.vtkDoubleArray()
            l_arr.SetName("Load")
            w_arr.SetName("Work")
            l_arr.SetNumberOfTuples(self.__n_ranks)
            w_arr.SetNumberOfTuples(self.__n_ranks)
            loads.append(l_arr)
            works.append(w_arr)

        # Create attribute data arrays for edge sent volumes
        volumes = []
        for i, sent in enumerate(distributions["sent"]):
            # Reduce directed edges into undirected ones
            u_edges = {}
            for k, v in sent.items():
                u_edges[frozenset(k)] = u_edges.setdefault(
                    frozenset(k), 0.) + v

            # Create and append new volume array for edges
            v_arr = vtk.vtkDoubleArray()
            v_arr.SetName("Largest Directed Volume")
            v_arr.SetNumberOfTuples(n_e)
            volumes.append(v_arr)
            
            # Assign edge volume values
            self.__logger.debug(f"\titeration {i} edges:")
            for e in range(n_e):
                v_arr.SetTuple1(e, u_edges.get(
                    self.__index_to_edge[e], float("nan")))
                self.__logger.debug(
                    f"\t {e} {self.__index_to_edge[e]}): {v_arr.GetTuple1(e)}")

        # Create grid streamer
        streamer = GridStreamer(self.__rank_points, self.__rank_lines, self.__field_data, [loads, works], volumes, lgr=self.__logger)

        # Write to ExodusII file when possible
        if streamer.Error:
            self.__logger.error(f"Failed to instantiate a grid streamer for file {self.__rank_file_name}")
            raise SystemExit(1)
        else:
            self.__logger.info(f"Writing ExodusII file: {self.__rank_file_name}")
            writer = vtk.vtkExodusIIWriter()
            writer.SetFileName(self.__rank_file_name)
            writer.SetInputConnection(streamer.Algorithm.GetOutputPort())
            writer.WriteAllTimeStepsOn()
            writer.Update()

    def write_object_view_file(self, distributions: dict):
        """ Map objects to grid and write ExodusII file."""
        # Determine available dimensions for object placement in ranks
        rank_dims = [d for d in range(3) if self.__grid_size[d] > 1]

        # Compute constant per object jitter
        jitter_dims = {
            i: [(random.random() - 0.5) * self.__object_jitter
                if d in rank_dims else 0.0 for d in range(3)]
            for i in self.__phases[0].get_object_ids()}

        # Determine whether phase must be updated
        update_phase = True if len(distributions["objects"]
            ) == len(self.__phases) else False
        
        # Iterate over all object distributions
        phase = self.__phases[0]
        for iteration, object_mapping in enumerate(distributions["objects"]):
            # Update phase when required
            if update_phase:
                phase = self.__phases[iteration]

            # Retrieve number of mesh points and bail out early if empty set
            n_o = phase.get_number_of_objects()
            if not n_o:
                self.__logger.warning("Empty list of objects, cannot write a mesh file")
                return

            # Compute number of communication edges
            n_e = int(n_o * (n_o - 1) / 2)
            self.__logger.info(
                f"Creating object view mesh with {n_o} points, " +
                f"{n_e} edges, and jitter factor: {self.__object_jitter}")
            
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
                n_o_per_dim = math.ceil(n_o_rank ** (1. / len(rank_dims)))
                self.__logger.debug(f"Arranging a maximum of {n_o_per_dim} objects per dimension in {rank_dims}")
                o_resolution = self.__grid_resolution / (n_o_per_dim + 1.)
                rank_size = [n_o_per_dim if d in rank_dims else 1 for d in range(3)]
                centering = [0.5 * o_resolution * (n_o_per_dim - 1.)
                             if d in rank_dims else 0.0 for d in range(3)]

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
                            jitter_dims[o.get_id()][d] + c) * o_resolution
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
            self.__logger.debug(f"\titeration {iteration} edges:")
            for e in range(n_e):
                v_arr.SetTuple1(e, edges.get(index_to_edge[e], float("nan")))
                self.__logger.debug(f"\t {e} {index_to_edge[e]}): {v_arr.GetTuple1(e)}")

            # Create VTK polygonal data mesh
            pd_mesh = vtk.vtkPolyData()
            pd_mesh.SetPoints(points)
            pd_mesh.GetPointData().SetScalars(t_arr)
            pd_mesh.GetPointData().AddArray(b_arr)
            pd_mesh.SetLines(lines)
            pd_mesh.GetCellData().SetScalars(v_arr)

            # Write to VTP file
            file_name = f"{self.__object_file_name}_{iteration:02d}.vtp"
            self.__logger.info(f"Writing VTP file: {file_name}")
            writer = vtk.vtkXMLPolyDataWriter()
            writer.SetFileName(file_name)
            writer.SetInputData(pd_mesh)
            writer.Update()

    def write(self, distributions: dict):
        """ Write rank and object ExodusII files."""

        # Write rank view file with global per-rank statistics
        self.write_rank_view_file(distributions)

        # Write object view file
        self.write_object_view_file(distributions)
