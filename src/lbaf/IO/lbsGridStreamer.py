from typing import Optional

import vtk

from ..Utils.lbsLogging import Logger, get_logger


class GridStreamer:
    """A class containing to stream a grid with time-varying attributes."""

    def __init__(
        self,
        points: vtk.vtkPoints,
        lines: vtk.vtkCellArray,
        field_arrays: Optional[dict] = None,
        point_arrays: Optional[list] = None,
        cell_arrays: Optional[list] = None,
        logger: Logger = None):
        """Class constructor."""
        # Defaults
        if field_arrays is None:
            field_arrays = {}
        if point_arrays is None:
            point_arrays = []
        if cell_arrays is None:
            cell_arrays = []

        # Assign logger to instance variable
        self.__logger = logger

        # Sanity checks
        self.error = False
        if not isinstance(points, vtk.vtkPoints):
            self.__logger.error("A vtkPoints instance is required as points input")
            self.error = True
            return
        if not isinstance(lines, vtk.vtkCellArray):
            self.__logger.error("A vtkCellArray instance is required as lines input")
            self.error = True
            return
        if not isinstance(field_arrays, dict):
            self.__logger.error("A dict of vtkDataArray instances is required as field data input")
            self.error = True
        if not isinstance(point_arrays, list):
            self.__logger.error("A list of dicts of vtkDataArray instances is required as point data input")
            self.error = True
            return
        if not isinstance(cell_arrays, list):
            self.__logger.error("A list of vtkDataArray instances is required as cell data input")
            self.error = True
            return

        # Keep track of requested number of steps and check consistency
        if any([(n_steps := len(cell_arrays)) != len(point_arrays)]):
            self.__logger.error(f"Number of point array dicts not all equal to {n_steps}")
            self.error = True
            return

        # More sanity checks
        for f_name, f_list in field_arrays.items():
            if n_steps != len(f_list):
                self.__logger.error(f"Number of {f_name} arrays and data arrays do not match: {len(f_list)} <> {n_steps}")
                self.error = True
                return

        # Instantiate the streaming source
        self.__logger.info(f"Streaming {n_steps} load-balancing steps")
        self.algorithm = vtk.vtkProgrammableSource()

        # Set source information
        info = self.algorithm.GetExecutive().GetOutputInformation().GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_RANGE(),
                 [0, n_steps - 1], 2)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS(),
                 range(n_steps), n_steps)

        # Implement RequestData() method for VTK pipeline
        def request_data_method():
            # Retrieve information vector
            info = self.algorithm.GetExecutive().GetOutputInformation().GetInformationObject(0)

            # Make the source is able to provide time steps
            output = self.algorithm.GetPolyDataOutput()
            t_s = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP())
            output.GetInformation().Set(vtk.vtkDataObject.DATA_TIME_STEP(), t_s)

            # Assign geometry and topology of output
            output.SetPoints(points)
            output.SetLines(lines)

            # Assign topology and field data to output for timestep index
            i = int(t_s)
            for f_name, f_list in field_arrays.items():
                if n_steps != len(f_list):
                    get_logger().error(
                        f"Number of {f_name} arrays and data arrays do not match: {len(f_list)} <> {n_steps}")
                    self.error = True
                    return
                output.GetFieldData().AddArray(f_list[i])

            # Assign data attributes to output for time step index
            for k, v in point_arrays[i].items():
                output.GetPointData().AddArray(v)
                self.__logger.debug(f"Added {k} point array")
            output.GetCellData().AddArray(cell_arrays[i])

        # Set VTK RequestData() to programmable source
        self.algorithm.SetExecuteMethod(request_data_method)
