########################################################################
lbsLoadWriterVT_module_aliases = {}
for m in [
    "csv",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsLoadWriterVT_module_aliases:
            globals()[lbsLoadWriterVT_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

from Model import lbsEpoch

########################################################################
class LoadWriterVT:
    """A class to write load directives for VT as CSV files with
    the following format:

      <iter/phase>, <object-id>, <time>

    Each file is named as <base-name>.<node>.out, where <node> spans the number
    of MPI ranks that VT is utilizing.

    Each line in a given file specifies the load of each object that must
    be mapped to that VT node for a given iteration/phase.
    """

  ####################################################################
    def __init__(self, e, f="lbs_out", s="vom"):
        """Class constructor:
        e: Epoch instance
        f: file name stem
        s: suffix
        """

        # Ensure that provided epoch has correct type
        if not isinstance(e, lbsEpoch.Epoch):
            print("** ERROR: [LoadWriterExodusII] Could not write to ExodusII file by lack of a LBS epoch")
            return

        # Assign internals
        self.epoch = e
        self.file_stem = "{}".format(f)
        self.suffix = s

    ####################################################################
    def write(self, time_step):
        """Write one CSV file per rank/procesor containing with one object
        per line, with the following format:

            <source processor>, <object-id>, <time>
        """

        # Iterate over processors
        for p in self.epoch.processors:
            # Create file name for current processor
            file_name = "{}.{}.{}.{}".format(
                self.file_stem,
                time_step,
                p.get_id(),
                self.suffix)
            
            # Count number of unsaved objects for sanity
            n_u = 0

            # Open output file
            with open(file_name, 'w') as f:
                # Create CSV writer
                writer = csv.writer(f, delimiter=',')

                # Iterate over objects
                for o in p.objects:
                    # Write object to file and increment count
                    try:
                        writer.writerow([o.get_source_processor(),
                                         o.get_id(),
                                         o.get_time()])
                    except:
                        n_u += 1

            # Sanity check
            if n_u:
                print("**  ERROR: {} objects could not be written to CSV file {}".format(
                    n_u,
                    file_name))
            else:
                print("[LoadWriterVT] Wrote {} objects to CSV file {}".format(
                    len(p.objects),
                    file_name))

########################################################################
