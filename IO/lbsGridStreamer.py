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
    def __init__(self, p, v, l):
        """Class constructor
        """

        # Sanity checks
        if not isinstance(p, vtk.vtkPoints):
            print "*  WARNING: A vtkPoints instance is required as input"
            self.Error = True
            return
        if not isinstance(v, vtk.vtkCellArray):
            print "*  WARNING: A vtkCellArray instance is required as input"
            self.Error = True
            return
        if not isinstance(l, list):
            print "*  WARNING: A list of vtkDataArray instances is required as input"
            self.Error = True
            return

        # Keep track of number of steps
        n_steps = len(l)

        # Instantiate the streaming source
        print "[GridStreamer] Streaming {} load-balancing steps".format(n_steps)
        self.Algorithm = vtk.vtkProgrammableSource()

        # Set source information
        info = self.Algorithm.GetExecutive().GetOutputInformation().GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_RANGE(),
                 [0, n_steps - 1], 2)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS(),
                 range(n_steps), n_steps)
        
        # Implement request information method
        def request_data_method():
            info = self.Algorithm.GetExecutive().GetOutputInformation().GetInformationObject(0)
            i = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP())

            output = self.Algorithm.GetPolyDataOutput()
            output.Initialize()
            output.GetInformation().Set(vtk.vtkDataObject.DATA_TIME_STEP(), i)

            # Assign topology and geometry to output
            output.SetPoints(p)
            output.SetVerts(v)

            # Assign data as both point and cell data
            output.GetPointData().AddArray(l[int(i)])
            output.GetCellData().AddArray(l[int(i)])

        self.Algorithm.SetExecuteMethod(request_data_method)
        self.Error = False

########################################################################





