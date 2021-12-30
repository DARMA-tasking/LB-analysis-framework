#
#@HEADER
###############################################################################
#
#                              lbsGridStreamer.py
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

import vtk

from src.Utils.logger import CLRS, logger


class GridStreamer:
    """A class containing to stream a grid with time-varying attributes
    """

    def __init__(self, points, lines, field_arrays, point_arrays, cell_arrays, lgr: Logger = None):
        """Class constructor
        """
        # Assign logger to instance variable
        self.lgr = lgr
        # Assign colors for logger
        self.grn = CLRS.get('green')
        self.red = CLRS.get('red')
        self.ylw = CLRS.get('yellow')

        # Sanity checks
        self.Error = False
        if not isinstance(points, vtk.vtkPoints):
            self.lgr.error(self.red("A vtkPoints instance is required as points input"))
            self.Error = True
            return
        if not isinstance(lines, vtk.vtkCellArray):
            self.lgr.error(self.red("A vtkCellArray instance is required as lines input"))
            self.Error = True
            return
        if not isinstance(field_arrays, dict):
            self.lgr.error(self.red("A dict of vtkDataArray instances is required as field data input"))
            self.Error = True
        if not isinstance(point_arrays, list):
            self.lgr.error(self.red("A list of vtkDataArray instances is required as point data input"))
            self.Error = True
            return
        if not isinstance(cell_arrays, list):
            self.lgr.error(self.red("A list of vtkDataArray instances is required as cell data input"))
            self.Error = True
            return

        # Keep track of requested number of steps and check consistency
        n_steps = len(cell_arrays)
        if any([n_steps != len(p) for p in point_arrays]):
            self.lgr.error(self.red(f"Number of time steps not all equal to {n_steps}"))
            self.Error = True
            return

        # More sanity checks
        for f_name, f_list in field_arrays.items():
            if n_steps != len(f_list):
                self.lgr.error(self.red(f"Number of {f_name} arrays and data arrays do not match: {len(f_list)} <> "
                                        f"{n_steps}"))
                self.Error = True
                return

        # Instantiate the streaming source
        self.lgr.info(self.grn(f"Streaming {n_steps} load-balancing steps"))
        self.Algorithm = vtk.vtkProgrammableSource()

        # Set source information
        info = self.Algorithm.GetExecutive().GetOutputInformation().GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_RANGE(),
                 [0, n_steps - 1], 2)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS(),
                 range(n_steps), n_steps)

        # Implement RequestData() method for VTK pipeline
        def request_data_method():
            # Retrieve information vector
            info = self.Algorithm.GetExecutive().GetOutputInformation().GetInformationObject(0)

            # Make the source is able to provide time steps
            output = self.Algorithm.GetPolyDataOutput()
            t_s = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP())
            output.GetInformation().Set(vtk.vtkDataObject.DATA_TIME_STEP(), t_s)

            # Assign geometry and topology of output
            output.SetPoints(points)
            output.SetLines(lines)

            # Assign topology and field data to output for timestep index
            i = int(t_s)
            for f_name, f_list in field_arrays.items():
                if n_steps != len(f_list):
                    logger().error(CLRS.get('red')(f"Number of {f_name} arrays and data arrays do not match: "
                                                   f"{len(f_list)} <> {n_steps}"))
                    self.Error = True
                    return
                output.GetFieldData().AddArray(f_list[i])

            # Assign data attributes to output for timestep index
            for p in point_arrays:
                output.GetPointData().AddArray(p[i])
            output.GetCellData().AddArray(cell_arrays[i])

        # Set VTK RequestData() to programmable source
        self.Algorithm.SetExecuteMethod(request_data_method)
