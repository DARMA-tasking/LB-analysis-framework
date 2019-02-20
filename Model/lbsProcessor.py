########################################################################
lbsProcessor_module_aliases = {
    "random": "rnd",
    }
for m in [
    "random",
    "sys",
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsProcessor_module_aliases:
            globals()[lbsProcessor_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False
 
from Model import lbsObject

########################################################################
class Processor:
    """A class representing a processor to which objects are assigned
    """

    ####################################################################
    def __init__(self, i, o=set()):
        # Member variables passed by constructor
        self.index   = i
        self.objects = set()
        for obj in o: 
            self.add_object(obj)

        # No underload information is known initially
        self.underloaded = set()
        self.underloads = {}

    ####################################################################
    def get_id(self):
        """Return processor ID
        """

        return self.index

    ####################################################################
    def get_object_ids(self):
        """Return IDs of objects assigned to processor
        """

        return [o.get_id() for o in self.objects]

    ####################################################################
    def add_object(self, o):
        """Assign object to processor
        """

        # Assert that object has the expected type
        if not isinstance(o, lbsObject.Object):
            print "*  WARNING: attempted to add object of incorrect type {}. Ignoring it.".format(type(o))
            return

        # Passed object has expected type, add it
        self.objects.add(o)

    ####################################################################
    def get_load(self):
        """Return total load assigned to processor
        """

        return sum([o.get_time() for o in self.objects])

    ####################################################################
    def initialize_underloads(self, procs, l_ave, f):
        """Initialize underloads when needed to sample of selected peers
        """

        # Retrieve current load on this processor
        l = self.get_load()

        # Initialize underload information at first pass
        if l < l_ave:
            self.underloaded = set([self.index])
            self.underloads[self.index] = l
            
            # Send underloads load to pseudo-random sample of procs
            return rnd.sample(procs, f), (self.underloaded, self.underloads)
            
        # This processor is not underloaded if this point was reached
        return [], None

    ####################################################################
    def forward_underloads(self, procs, f):
        """Formard underloads when received to sample of selected peers
        """

        # Retrieve current load on this processor
        l = self.get_load()

        # Propagate load only if needed
        if l < l_ave:
            # Initialize underload information at first pass
            if not self.underloaded:
                self.underloaded.add = set([self.index])
                self.underloads[self.index] = l
            
            # Propagate load to pseudo-random sample of selected peers
            selected = procs.difference(self.underloaded)
            return rnd.sample(selected, f), (self.underloaded, self.underloads)

        # This processor is not underloaded if this point was reached
        return None, None

    ####################################################################
    def process_message(self, msg):
        """Update internal when message is received
        """

        # Sanity check
        if len(msg) < 2:
            print "*  WARNING: incomplete message: {}. Ignoring it.".format(msg)
            return

        # Union received set of underloaded procs with current one
        self.underloaded.update(msg[0])

        # Update underload information
        self.underloads.update(msg[1])

        # Sanity check
        l1 = len(self.underloaded)
        l2 = len(self.underloads)
        if l1 != l2:
            print "** ERROR: cannot process message {} at processor {}. Exiting.".format(msg, self.get_id())
            sys.exit(1)

    ####################################################################
    def compute_cmf_underloads(self, l_ave, pmf_type=0):
        """Compute CMF of underloads given an average load
        """

        # Initialize CMF
        cmf = []

        # Distinguish between different PMF types
        if not pmf_type:
            # Initialize ancillary values 
            sum_p = 0.
            inv_l_ave = 1. / l_ave

            # Iterate over all underloads
            for l in self.underloads.values():
                # Update CMF
                sum_p += 1. - inv_l_ave * l

                # Assign CMF for current underloaded processor
                cmf.append(sum_p)

            # Normalize and return CMF
            return map(lambda x: x / sum_p, cmf)

########################################################################
