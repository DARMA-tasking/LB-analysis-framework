#
#@HEADER
###############################################################################
#
#                             lbsWriterExodusII.py
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
from logging import Logger
import os
import vtk

from src.IO.lbsGridStreamer import GridStreamer
from src.Model.lbsPhase import Phase


class WriterExodusII:
    """A class to write LBS data to Exodus II files via VTK layer
    """

    def __init__(self, p: Phase, m, f="lbs_out", s='e', r=1., output_dir=None, logger: Logger = None):
        """ Class constructor:
            p: Phase instance
            m: Rank dictionary
            f: file name stem
            s: suffix
            r: grid_resolution value
            output_dir: output directory
        """

        # Assign logger to instance variable
        self.__lgr = logger

        # Ensure that provided phase has correct type
        if not isinstance(p, Phase):
            self.__lgr.error("Could not write to ExodusII file by lack of a LBS phase")
            return
        self.__phase = p

        # If no rank mapping was provided, do not do anything
        if not callable(m):
            self.__lgr.error("Could not write to ExodusII file by lack of a rank mapping")
            return
        self.__mapping = m

        # Assemble file name from constructor parameters
        self.__file_name = f"{f}.{s}"
        self.__output_dir = output_dir
        if self.__output_dir is not None:
            self.__file_name = os.path.join(self.__output_dir, self.__file_name)

        # Grid_resolution between points
        try:
            self.__grid_resolution = float(r)
        except:
            self.__grid_resolution = 1.

    def write(self, load_statistics, load_distributions, volume_distributions, work_distributions):
        """ Map ranks to grid and write ExodusII file
        """

        # Retrieve number of mesh points and bail out early if empty set
        n_p = len(self.__phase.get_ranks())
        if not n_p:
            self.__lgr.error("Empty list of ranks, cannot write a mesh file")
            return

        # Number of edges is fixed due to vtkExodusIIWriter limitation
        n_e = int(n_p * (n_p - 1) / 2)
        self.__lgr.info(f"Creating mesh with {n_p} points and {n_e} edges")

        # Create and populate field data arrays for load statistics
        time_stats = {}
        for stat_name, stat_values in load_statistics.items():
            # Create one singleton for each value of each statistic
            for v in stat_values:
                s_arr = vtk.vtkDoubleArray()
                s_arr.SetNumberOfTuples(1)
                s_arr.SetTuple1(0, v)
                s_arr.SetName(stat_name)
                time_stats.setdefault(stat_name, []).append(s_arr)

        # Create attribute data arrays for rank loads and works
        time_loads, time_works = [], []
        for _, _ in zip(load_distributions, work_distributions):
            # Create and append new load and work point arrays
            l_arr, w_arr = vtk.vtkDoubleArray(), vtk.vtkDoubleArray()
            l_arr.SetName("Load")
            w_arr.SetName("Work")
            l_arr.SetNumberOfTuples(n_p)
            w_arr.SetNumberOfTuples(n_p)
            time_loads.append(l_arr)
            time_works.append(w_arr)

        # Iterate over ranks and create mesh points
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(n_p)
        for i, p in enumerate(self.__phase.get_ranks()):
            # Insert point based on Cartesian coordinates
            points.SetPoint(i, [self.__grid_resolution * c for c in self.__mapping(p)])
            for l, (l_arr, w_arr) in enumerate(zip(time_loads, time_works)):
                l_arr.SetTuple1(i, load_distributions[l][i])
                w_arr.SetTuple1(i, work_distributions[l][i])

        # Iterate over all possible links and create edges
        lines = vtk.vtkCellArray()
        edge_indices = {}
        flat_index = 0
        for i in range(n_p):
            for j in range(i + 1, n_p):
                # Insert new link based on endpoint indices
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, j)
                lines.InsertNextCell(line)

                # Update flat index map
                edge_indices[flat_index] = frozenset([i, j])
                flat_index += 1

        # Create attribute data arrays for edge volumes
        time_volumes = []
        for i, volumes in enumerate(volume_distributions):
            # Reduce directed edges into undirected ones
            u_edges = {}
            for k, v in volumes.items():
                u_edges[frozenset(k)] = u_edges.setdefault(frozenset(k), 0.) + v

            # Create and append new volume array for edges
            v_arr = vtk.vtkDoubleArray()
            v_arr.SetName("Largest Directed Volume")
            v_arr.SetNumberOfTuples(n_e)
            time_volumes.append(v_arr)
            
            # Assign edge volume values
            self.__lgr.debug(f"\titeration {i} edges:")
            for e in range(n_e):
                v_arr.SetTuple1(e, u_edges.get(edge_indices[e], float("nan")))
                self.__lgr.debug(f"\t {e} {edge_indices[e]}): {v_arr.GetTuple1(e)}")

        # Create grid streamer
        streamer = GridStreamer(points, lines, time_stats, [time_loads, time_works], time_volumes, lgr=self.__lgr)

        # Write to ExodusII file when possible
        if streamer.Error:
            self.__lgr.error(f"Failed to instantiate a grid streamer for file {self.__file_name}")
        else:
            self.__lgr.info(f"Writing ExodusII file: {self.__file_name}")
            writer = vtk.vtkExodusIIWriter()
            writer.SetFileName(self.__file_name)
            writer.SetInputConnection(streamer.Algorithm.GetOutputPort())
            writer.WriteAllTimeStepsOn()
            writer.Update()
