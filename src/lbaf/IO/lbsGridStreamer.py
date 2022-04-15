from logging import Logger

import vtk

from ..Utils.logger import logger


class GridStreamer:
    """A class containing to stream a grid with time-varying attributes
    """

    def __init__(self, points, lines, field_arrays, point_arrays, cell_arrays, lgr: Logger = None):
        """Class constructor
        """
        # Assign logger to instance variable
        self.__logger = lgr

        # Sanity checks
        self.Error = False
        if not isinstance(points, vtk.vtkPoints):
            self.__logger.error("A vtkPoints instance is required as points input")
            self.Error = True
            return
        if not isinstance(lines, vtk.vtkCellArray):
            self.__logger.error("A vtkCellArray instance is required as lines input")
            self.Error = True
            return
        if not isinstance(field_arrays, dict):
            self.__logger.error("A dict of vtkDataArray instances is required as field data input")
            self.Error = True
        if not isinstance(point_arrays, list):
            self.__logger.error("A list of vtkDataArray instances is required as point data input")
            self.Error = True
            return
        if not isinstance(cell_arrays, list):
            self.__logger.error("A list of vtkDataArray instances is required as cell data input")
            self.Error = True
            return

        # Keep track of requested number of steps and check consistency
        n_steps = len(cell_arrays)
        if any([n_steps != len(p) for p in point_arrays]):
            self.__logger.error(f"Number of time steps not all equal to {n_steps}")
            self.Error = True
            return

        # More sanity checks
        for f_name, f_list in field_arrays.items():
            if n_steps != len(f_list):
                self.__logger.error(f"Number of {f_name} arrays and data arrays do not match: {len(f_list)} <> {n_steps}")
                self.Error = True
                return

        # Instantiate the streaming source
        self.__logger.info(f"Streaming {n_steps} load-balancing steps")
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
                    logger().error(f"Number of {f_name} arrays and data arrays do not match: {len(f_list)} <> "
                                   f"{n_steps}")
                    self.Error = True
                    return
                output.GetFieldData().AddArray(f_list[i])

            # Assign data attributes to output for time step index
            for p in point_arrays:
                output.GetPointData().AddArray(p[i])
            output.GetCellData().AddArray(cell_arrays[i])

        # Set VTK RequestData() to programmable source
        self.Algorithm.SetExecuteMethod(request_data_method)