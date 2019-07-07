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

from Model import lbsObject, lbsMessage
import time
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

        # No message was received initially
        self.round_last_received = 0

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
    def get_sent(self, exclude_self=True):
        """Aggregate all weights sent by processor by receiving object ID
        """

        return reduce(
            lambda x, y: {
                k: x.get(k, 0) + y.get(k, 0)
                for k in set(x.keys()).union(y.keys())},
            [o.get_sent_by_ids() for o in self.objects],
            {})

    ####################################################################
    def initialize_underloads(self, procs, l_ave, f):
        """Initialize underloads when needed to sample of selected peers
        """

        # Retrieve current load on this processor
        l = self.get_load()

        # Initialize underload information at first pass
        if l < l_ave:
            self.underloaded = set([self])
            self.underloads[self] = l

            # Create underload message tagged at first round
            msg = lbsMessage.Message(1, (self.underloaded, self.underloads))

            # Broadcast underloads to pseudo-random sample of procs
            return rnd.sample(procs, min(f, len(procs))), msg

        # This processor is not underloaded if this point was reached
        return [], None

    ####################################################################
    def forward_underloads(self, r, procs, f):
        """Formard underloads to sample of selected peers
        """

        # Compute complement of set of underloaded processors
        c_procs = procs.difference(self.underloaded)

        # Create underload message tagged at current round
        msg = lbsMessage.Message(r, (self.underloaded, self.underloads))

        # Forward underloads to pseudo-random sample of procs
        return rnd.sample(c_procs, min(f, len(c_procs))), msg

    ####################################################################
    def process_underload_message(self, msg):
        """Update internals when underload message is received
        """

        # Assert that message has the expected type
        if not isinstance(msg, lbsMessage.Message):
            print "*  WARNING: attempted to pass message of incorrect type {}. Ignoring it.".format(type(msg))

        # Retrieve information from message
        info = msg.get_content()
        if len(info) < 2:
            print "*  WARNING: incomplete message content: {}. Ignoring it.".format(info)
            return

        # Union received set of underloaded procs with current one
        self.underloaded.update(info[0])

        # Update underload information
        self.underloads.update(info[1])

        # Sanity check
        l1 = len(self.underloaded)
        l2 = len(self.underloads)
        if l1 != l2:
            print "** ERROR: cannot process message {} at processor {}. Exiting.".format(info, self.get_id())
            sys.exit(1)

        # Update last received message index
        self.round_last_received = msg.get_round()

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
