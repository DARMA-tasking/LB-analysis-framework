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
        print("** ERROR: failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Model import lbsPhase
from IO import lbsGridStreamer

########################################################################
class LoadWriterExodusII:
    """A class to write LBS data to Exodus II files via VTK layer
    """

  ####################################################################
    def __init__(self, e, m, f="lbs_out", s='e', gr=1.):
        """Class constructor:
        e: Phase instance
        m: Processor dictionnary
        f: file name stem
        s: suffix
        gr: grid_resolution value
        """

        # If VTK is not available, do not do anything
        if not has_vtk:
            print("** ERROR: Could not write to ExodusII file by lack of VTK")
            return

        # Ensure that provided phase has correct type
        if not isinstance(e, lbsPhase.Phase):
            print("** ERROR: Could not write to ExodusII file by lack of a LBS phase")
            return
        self.phase = e

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
    def write(self, load_statistics, load_distributions, weight_distributions, verbose=False):
        """Map processors to grid and write ExodusII file
        """

        # Retrieve number of mesh points and bail out early if empty set
        n_p = len(self.phase.processors)
        if not n_p:
            print("** ERROR: Empty list of processors, cannot write a mesh file")
            return

        # Number of edges is fixed due to vtkExodusIIWriter limitation
        n_e = n_p * (n_p - 1) / 2
        print("[LoadWriterExodusII] Creating mesh with {} points and {} edges".format(
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
        streamer = lbsGridStreamer.GridStreamer(
            points,
            lines,
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
