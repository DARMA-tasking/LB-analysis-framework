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
    """A class to write LBAF results to mesh files via VTK layer
    """

    def __init__(
        self,
        p: Phase,
        grid_size,
        object_jitter: float,
        logger: Logger,
        f="lbs_out",
        r=1.,
        output_dir=None
    ):
        """ Class constructor:
            p: Phase instance
            grid_size: iterable containing grid sizes in each dimension
            object_jitter: coefficient of random jitter with magnitude < 1
            f: file name stem
            r: grid_resolution value
            output_dir: output directory
        """
        # Assign logger to instance variable
        self.__logger = logger

        # Ensure that provided phase has correct type
        if not isinstance(p, Phase):
            self.__logger.error("Could not write to ExodusII file by lack of a LBS phase")
            raise SystemExit(1)
        self.__phase = p

        # Ensure that specified grid resolution is correct
        if not isinstance(r, numbers.Number) or r <= 0.:
            self.__logger.error("Grid resolution must be a positive number")
            raise SystemExit(1)
        self.__grid_resolution = float(r)

        # Keep track of mesh properties
        self.__n_p =  len(self.__phase.get_ranks())
        self.__grid_size = grid_size
        self.__object_jitter = object_jitter

        # Assemble file and path names from constructor parameters
        self.__rank_file_name = f"{f}_rank_view.e"
        self.__object_file_name = f"{f}_object_view"
        self.__output_dir = output_dir
        if self.__output_dir is not None:
            self.__rank_file_name = os.path.join(
                self.__output_dir,
                self.__rank_file_name)
            self.__object_file_name = os.path.join(
                self.__output_dir,
                self.__object_file_name)

    @staticmethod
    def global_id_to_cartesian(flat_id, grid_sizes):
        """ Map global index to its Cartesian grid coordinates
        """
        # Sanity check
        n01 = grid_sizes[0] * grid_sizes[1]
        if flat_id < 0 or flat_id >= n01 * grid_sizes[2]:
            return None, None, None

        # Compute successive Euclidean divisions
        k, r = divmod(flat_id, n01)
        j, i = divmod(r, grid_sizes[0])

        # Return Cartesian coordinates
        return i, j, k

    def write_rank_view_file(self, distributions: dict, statistics: dict):
        """ Map ranks to grid and write ExodusII file
        """
        # Number of edges is fixed due to vtkExodusIIWriter limitation
        n_e = int(self.__n_p * (self.__n_p - 1) / 2)
        self.__logger.info(f"Creating rank view mesh with {self.__n_p} points and {n_e} edges")

        # Create and populate global field arrays for statistics
        global_stats = {}
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
                global_stats.setdefault(stat_name, []).append(s_arr)

        # Create attribute data arrays for rank loads and works
        loads, works = [], []
        for _, _ in zip(distributions["load"], distributions["work"]):
            # Create and append new load and work point arrays
            l_arr, w_arr = vtk.vtkDoubleArray(), vtk.vtkDoubleArray()
            l_arr.SetName("Load")
            w_arr.SetName("Work")
            l_arr.SetNumberOfTuples(self.__n_p)
            w_arr.SetNumberOfTuples(self.__n_p)
            loads.append(l_arr)
            works.append(w_arr)

        # Iterate over ranks and create mesh points
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(self.__n_p)
        for i, p in enumerate(self.__phase.get_ranks()):
            # Insert point based on Cartesian coordinates
            points.SetPoint(i, [
                self.__grid_resolution * c
                for c in self.global_id_to_cartesian(
                    p.get_id(), self.__grid_size)])
            for l, (l_arr, w_arr) in enumerate(zip(loads, works)):
                l_arr.SetTuple1(i, distributions["load"][l][i])
                w_arr.SetTuple1(i, distributions["work"][l][i])

        # Iterate over all possible links and create edges
        lines = vtk.vtkCellArray()
        index_to_edge = {}
        edge_index = 0
        for i in range(self.__n_p):
            for j in range(i + 1, self.__n_p):
                # Insert new link based on endpoint indices
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, j)
                lines.InsertNextCell(line)

                # Update flat index map
                index_to_edge[edge_index] = frozenset([i, j])
                edge_index += 1

        # Create attribute data arrays for edge sent volumes
        volumes = []
        for i, sent in enumerate(distributions["sent"]):
            # Reduce directed edges into undirected ones
            u_edges = {}
            for k, v in sent.items():
                u_edges[frozenset(k)] = u_edges.setdefault(frozenset(k), 0.) + v

            # Create and append new volume array for edges
            v_arr = vtk.vtkDoubleArray()
            v_arr.SetName("Largest Directed Volume")
            v_arr.SetNumberOfTuples(n_e)
            volumes.append(v_arr)
            
            # Assign edge volume values
            self.__logger.debug(f"\titeration {i} edges:")
            for e in range(n_e):
                v_arr.SetTuple1(e, u_edges.get(index_to_edge[e], float("nan")))
                self.__logger.debug(f"\t {e} {index_to_edge[e]}): {v_arr.GetTuple1(e)}")

        # Create grid streamer
        streamer = GridStreamer(points, lines, global_stats, [loads, works], volumes, lgr=self.__logger)

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
        """ Map objects to grid and write ExodusII file
        """

        # Retrieve number of mesh points and bail out early if empty set
        n_o = self.__phase.get_number_of_objects()
        if not n_o:
            self.__logger.error("Empty list of objects, cannot write a mesh file")
            return

        # Number of edges is fixed due to vtkExodusIIWriter limitation
        n_e = int(n_o * (n_o - 1) / 2)
        self.__logger.info(
            f"Creating object view mesh with {n_o} points, " +
            f"{n_e} edges, and jitter factor: {self.__object_jitter}")

        # Determine available dimensions for object placement in ranks
        rank_dims = [d for d in range(3) if self.__grid_size[d] > 1]

        # Compute constant per object jitter
        jitter_dims = {
            i: [(random.random() - 0.5) * self.__object_jitter
                if d in rank_dims else 0.0 for d in range(3)]
            for i in self.__phase.get_object_ids()}

        # Iterate over all object distributions
        for iteration, object_mapping in enumerate(distributions["objects"]):
            # Create point array for object times
            t_arr = vtk.vtkDoubleArray()
            t_arr.SetName("Time")
            t_arr.SetNumberOfTuples(n_o)

            # Iterate over ranks and objects to create mesh points
            points = vtk.vtkPoints()
            points.SetNumberOfPoints(n_o)
            point_to_index = {}
            index_to_point = []
            point_index = 0
            sent_volumes = []
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
                    
                for i, o in enumerate(objects):
                    # Insert point using offset and rank coordinates
                    points.SetPoint(point_index, [
                        offsets[d] - centering[d] + (
                            jitter_dims[o.get_id()][d] + c) * o_resolution
                        for d, c in enumerate(self.global_id_to_cartesian(
                            i, rank_size))])
                    t_arr.SetTuple1(point_index, o.get_time())

                    # Update sent volumes
                    for k, v in o.get_sent().items():
                        sent_volumes.append((point_index, k, v))

                    # Update maps and counters
                    point_to_index[o] = point_index
                    index_to_point.append(o)
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
            pd_mesh.SetLines(lines)
            pd_mesh.GetCellData().SetScalars(v_arr)

            # Write to VTP file
            file_name = f"{self.__object_file_name}_{iteration:02d}.vtp"
            self.__logger.info(f"Writing VTP file: {file_name}")
            writer = vtk.vtkXMLPolyDataWriter()
            writer.SetFileName(file_name)
            writer.SetInputData(pd_mesh)
            writer.Update()

    def write(self, distributions: dict, statistics: dict):
        """ Write rank and object ExodusII files
        """
        # Write rank view file with global per-rank statistics
        self.write_rank_view_file(distributions, statistics)

        # Write object view file
        self.write_object_view_file(distributions)
