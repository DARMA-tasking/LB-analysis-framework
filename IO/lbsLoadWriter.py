########################################################################
lbsLoadWriter_module_aliases = {}
for m in [
    "vtk",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsLoadWriter_module_aliases:
            globals()[lbsLoadWriter_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

from Model import lbsEpoch
from IO import lbsGridStreamer

########################################################################
class LoadWriter:
    """A class to write LBS data to Exodus II files via VTK layer
    """

  ####################################################################
    def __init__(self, e, m, n, s=1.0):
        """Class constructor:
        e: Epoch instance
        m: Processor dict
        n: file name string
        s: spacing value
        """

        # If VTK is not available, do not do anything
        if not has_vtk:
            print "*  WARNING: Could not write to ExodusII file by lack of VTK"
            return

        # If no LBS epoch was provided, do not do anything
        if not isinstance(e, lbsEpoch.Epoch):
            print "*  WARNING: Could not write to ExodusII file by lack of a LBS epoch"
            return
        else:
            self.epoch = e

        # If no processor mapping was provided, do not do anything
        if not callable(m):
            print "*  WARNING: Could not write to ExodusII file by lack of a processor mapping"
            return
        else:
            self.mapping = m

        # Try to retrieve output file name from constructor parameter
        try:
            self.file_name = "{}".format(n)
        except:
            self.file_name = "lbs_out.e"

        # Spacing between points
        try:
            self.spacing = float(s)
        except:
            self.spacing = 1.0

    ####################################################################
    def write(self, load_statistics, load_distributions):
        """Map processors to grid and write ExodusII file
        """
        # Retrieve epoch processors
        procs = self.epoch.processors
        n_p = len(procs)

        # Create storage for statistics
        stats = vtk.vtkFieldData()

        # Create storage for points at processors
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(n_p)

        # Create storage for vertices at processors
        vertices = vtk.vtkCellArray()

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

        # Iterate over processors and populate grid
        for i, p in enumerate(procs):
            points.SetPoint(i, [self.spacing * c for c in self.mapping(p)])
            vertices.InsertNextCell(1, [i])
            for l, l_arr in enumerate(load_arrays):
                l_arr.SetTuple1(i, load_distributions[l][i])

        # Create grid streamer
        streamer = lbsGridStreamer.GridStreamer(points,
                                                vertices,
                                                stat_arrays,
                                                load_arrays)

        # Write to ExodusII file
        print "[LoadWriter] Writing ExodusII mesh \"{}\"".format(self.file_name)
        writer = vtk.vtkExodusIIWriter()
        writer.SetFileName(self.file_name)
        writer.SetInputConnection(streamer.Algorithm.GetOutputPort())
        writer.WriteAllTimeStepsOn()
        writer.Update()

        # Sanity check
        if streamer.Error:
            print "*  WARNING: Failed to write \"{}\"".format(self.file_name)

########################################################################
