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
import os
import bcolors
import vtk

from src.IO.lbsGridStreamer import GridStreamer
from src.Model.lbsPhase import Phase


class WriterExodusII:
    """A class to write LBS data to Exodus II files via VTK layer
    """

    def __init__(self, e, m, f="lbs_out", s='e', r=1., output_dir=None):
        """Class constructor:
        e: Phase instance
        m: Rank dictionnary
        f: file name stem
        s: suffix
        r: grid_resolution value
        output_dir: output directory
        """

        # Ensure that provided phase has correct type
        if not isinstance(e, Phase):
            print(bcolors.ERR
                + "*  ERROR: Could not write to ExodusII file by lack of a LBS phase"
                + bcolors.END)
            return
        self.phase = e

        # If no processor mapping was provided, do not do anything
        if not callable(m):
            print(bcolors.ERR
                + "*  ERROR: Could not write to ExodusII file by lack of a processor mapping"
                + bcolors.END)
            return
        self.mapping = m

        # Assemble file name from constructor paramters
        self.file_name = "{}.{}".format(f, s)
        self.output_dir = output_dir
        if self.output_dir is not None:
            self.file_name = os.path.join(self.output_dir, self.file_name)

        # Grid_resolution between points
        try:
            self.grid_resolution = float(r)
        except:
            self.grid_resolution = 1.

    def write(self, load_statistics, load_distributions, weight_distributions, verbose=False):
        """Map processors to grid and write ExodusII file
        """

        # Retrieve number of mesh points and bail out early if empty set
        n_p = len(self.phase.processors)
        if not n_p:
            print(bcolors.ERR
                + "*  ERROR: Empty list of processors, cannot write a mesh file"
                + bcolors.END)
            return

        # Number of edges is fixed due to vtkExodusIIWriter limitation
        n_e = int(n_p * (n_p - 1) / 2)
        print(bcolors.HEADER
            + "[WriterExodusII] "
            + bcolors.END
            + "Creating mesh with {} points and {} edges".format(
            n_p,
            n_e))

        # Create and populate field data arrays for load statistics
        stat_arrays = {}
        for stat_name, stat_values in load_statistics.items():
            # Create one singleton for each value of each statistic
            for v in stat_values:
                s_arr = vtk.vtkDoubleArray()
                s_arr.SetNumberOfTuples(1)
                s_arr.SetTuple1(0, v)
                s_arr.SetName(stat_name)
                stat_arrays.setdefault(stat_name, []).append(s_arr)

        # Create attribute data arrays for processors loads
        load_arrays = []
        for _ in load_distributions:
            # Create and append new load array for points
            l_arr = vtk.vtkDoubleArray()
            l_arr.SetName("Load")
            l_arr.SetNumberOfTuples(n_p)
            load_arrays.append(l_arr)

        # Iterate over processors and create mesh points
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(n_p)
        for i, p in enumerate(self.phase.processors):
            # Insert point based on Cartesian coordinates
            points.SetPoint(
                i,
                [self.grid_resolution * c for c in self.mapping(p)])
            for l, l_arr in enumerate(load_arrays):
                l_arr.SetTuple1(i, load_distributions[l][i])

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

        # Create attribute data arrays for edge weights
        weight_arrays = []
        for i, w in enumerate(weight_distributions):
            # Create and append new weight array for edges
            w_arr = vtk.vtkDoubleArray()
            w_arr.SetName("Weight")
            w_arr.SetNumberOfTuples(n_e)
            weight_arrays.append(w_arr)
            
            # Assign edge weight values
            if verbose:
                print("\titeration {} edges:".format(i))
            for e in range(n_e):
                w_arr.SetTuple1(e, w.get(edge_indices[e], float("nan")))
                if verbose:
                    print("\t {} ({}): {}".format(
                        e,
                        list(edge_indices[e]),
                        w_arr.GetTuple1(e)))

        # Create grid streamer
        streamer = GridStreamer(
            points,
            lines,
            stat_arrays,
            load_arrays,
            weight_arrays)

        # Write to ExodusII file when possible
        if streamer.Error:
            print(bcolors.ERR
                + "*  ERROR: Failed to instantiate a grid streamer for file {}".format(
                self.file_name)
                + bcolors.END)
        else:
            print(bcolors.HEADER
                + "[WriterExodusII] "
                + bcolors.END
                + "Writing ExodusII file: {}".format(
                self.file_name))
            writer = vtk.vtkExodusIIWriter()
            writer.SetFileName(self.file_name)
            writer.SetInputConnection(streamer.Algorithm.GetOutputPort())
            writer.WriteAllTimeStepsOn()
            writer.Update()
