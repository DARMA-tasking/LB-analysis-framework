########################################################################
lbsGridStreamer_module_aliases = {}
for m in [
    "vtk",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsGridStreamer_module_aliases:
            globals()[lbsGridStreamer_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

########################################################################
class GridStreamer:
    """A class containing to stream a grid with time-varying attributes
    """

  ####################################################################
    def __init__(self, points, verts, field_arrays, data_arrays):
        """Class constructor
        """

        # Sanity checks
        self.Error = False
        if not isinstance(points, vtk.vtkPoints):
            print "** ERROR: A vtkPoints instance is required as points input"
            self.Error = True
            return
        if not isinstance(verts, vtk.vtkCellArray):
            print "** ERROR: A vtkCellArray instance is required as vertices input"
            self.Error = True
            return
        if not isinstance(field_arrays, dict):
            print "** ERROR: A dict of vtkDataArray instances is required as field data input"
            self.Error = True
        if not isinstance(data_arrays, list):
            print "** ERROR: A list of vtkDataArray instances is required as cell/point data input"
            self.Error = True
            return

        # Keep track of requested number of steps
        n_steps = len(data_arrays)

        # More sanity checks
        for f_name, f_list in field_arrays.items():
            if n_steps != len(f_list):
                print "** ERROR: Number of {} arrays and data arrays do not match: {} <> {}".format(
                    f_name,
                    len(f_list),
                    n_steps)
                self.Error = True
                return

        # Instantiate the streaming source
        print "[GridStreamer] Streaming {} load-balancing steps".format(n_steps)
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

            # Assign topology and geometry to output
            output.SetPoints(points)
            output.SetVerts(verts)

            # Assign field data to output for timestep index
            i = int(t_s)
            for f_name, f_list in field_arrays.items():
                if n_steps != len(f_list):
                    print "** ERROR: Number of {} arrays and data arrays do not match: {} <> {}".format(
                        f_name,
                        len(f_list),
                        n_steps)
                    self.Error = True
                    return
                output.GetFieldData().AddArray(f_list[i])

            # Assign data attributes to output for timestep index
            d_arr = data_arrays[i]
            output.GetPointData().AddArray(d_arr)
            output.GetCellData().AddArray(d_arr)

        # Set VTK RequestData() to programmable source
        self.Algorithm.SetExecuteMethod(request_data_method)

########################################################################





