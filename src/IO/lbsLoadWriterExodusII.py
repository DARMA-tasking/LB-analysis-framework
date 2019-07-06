########################################################################
lbsLoadWriterExodusII_module_aliases = {}
for m in [
    "vtk",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsLoadWriterExodusII_module_aliases:
            globals()[lbsLoadWriterExodusII_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

from Model import lbsEpoch
from IO import lbsGridStreamer

########################################################################
class LoadWriterExodusII:
    """A class to write LBS data to Exodus II files via VTK layer
    """

  ####################################################################
    def __init__(self, e, m, f="lbs_out", s='e', gr=1.):
        """Class constructor:
        e: Epoch instance
        m: Processor dictionnary
        f: file name stem
        s: suffix
        gr: grid_resolution value
        """

        # If VTK is not available, do not do anything
        if not has_vtk:
            print("** ERROR: Could not write to ExodusII file by lack of VTK")
            return

        # Ensure that provided epoch has correct type
        if not isinstance(e, lbsEpoch.Epoch):
            print("** ERROR: Could not write to ExodusII file by lack of a LBS epoch")
            return
        self.epoch = e

        # If no processor mapping was provided, do not do anything
        if not callable(m):
            print("** ERROR: Could not write to ExodusII file by lack of a processor mapping")
            return
        self.mapping = m

        # Assemble file name from constructor paramters
        self.file_name = "{}.{}".format(f, s)

        # Grid_resolution between points
        try:
            self.grid_resolution = float(gr)
        except:
            self.grid_resolution = 1.

    ####################################################################
    def write(self, load_statistics, load_distributions, weight_distributions):
        """Map processors to grid and write ExodusII file
        """

        # Retrieve number of epoch processors
        n_p = len(self.epoch.processors)

        # Create storage for statistics
        stats = vtk.vtkFieldData()

        # Create storage for points at processors
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(n_p)

        # Create storage for edges between processors
        edges = vtk.vtkCellArray()

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
            l_arr = vtk.vtkDoubleArray()
            l_arr.SetNumberOfTuples(n_p)
            l_arr.SetName("Load")
            load_arrays.append(l_arr)

        # Create attribute data arrays for edge weights
        weight_arrays = []
        n_e = n_p * (n_p - 1)
        for _ in weight_distributions:
            w_arr = vtk.vtkDoubleArray()
            w_arr.SetNumberOfTuples(n_e)
            w_arr.SetName("Weight")
            weight_arrays.append(w_arr)

        # Iterate over processors and populate grid
        for i, p in enumerate(self.epoch.processors):
            points.SetPoint(i, [self.grid_resolution * c for c in self.mapping(p)])
            #edges.InsertNextCell(2, [i, i])
            for l, l_arr in enumerate(load_arrays):
                l_arr.SetTuple1(i, load_distributions[l][i])

        # the second 0 is the index of the Origin in linesPolyData's points
        # 2 is the index of P1 in linesPolyData's points
        #line = vtkLine()
        #line.GetPointIds().SetId(0, 0)
        #line.GetPointIds().SetId(1, 2)
        #lines.InsertNextCell(line)

        # Create grid streamer
        streamer = lbsGridStreamer.GridStreamer(
            points,
            edges,
            stat_arrays,
            load_arrays,
            weight_arrays)

        # Write to ExodusII file when possible
        if streamer.Error:
            print("** ERROR: Failed to instantiate a grid streamer for file {}".format(
                self.file_name))
        else:
            print("[LoadWriterExodusII] Writing ExodusII file: {}".format(
                self.file_name))
            writer = vtk.vtkExodusIIWriter()
            writer.SetFileName(self.file_name)
            writer.SetInputConnection(streamer.Algorithm.GetOutputPort())
            writer.WriteAllTimeStepsOn()
            writer.Update()

########################################################################
