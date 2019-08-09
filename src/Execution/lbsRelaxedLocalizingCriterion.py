########################################################################
from lbsCriterionBase import CriterionBase

########################################################################
class RelaxedLocalizingCriterion(CriterionBase):
    """A concrete class for a relaxedly localizing criterion
    """

    ####################################################################
    def __init__(self, processors, edges, _):
        """Class constructor:
        processors: set of processors (lbsProcessor.Processor instances)
        edges: dictionary of edges (frozensets)
        _: no parameters dictionary needed for this criterion
        """

        # Call superclass init
        super(RelaxedLocalizingCriterion, self).__init__(processors, edges)
        print("[RelaxedLocalizingCriterion] Instantiated concrete criterion")
        
    ####################################################################
    def is_satisfied(self, object, p_src, p_dst):
        """A criterion allowing for local disruptions for more locality 
        """

        # Retrieve object communications
        comm = object.get_communicator()
        sent = comm.get_sent().items()
        recv = comm.get_received().items()

        # Retrieve ID of processor to which an object is assigned
        p_id = (lambda x: x.get_processor_id())

        # Test whether first component is source processor
        is_s = (lambda x: p_id(x[0]) == p_src.get_id())

        # Test whether first component is destination processor
        is_d = (lambda x: p_id(x[0]) == p_dst.get_id())

        # Add value with second components of a collection
        xPy1 = (lambda x, y: x + y[1])

        # Aggregate communication weights with source
        w_src = reduce(xPy1,
                       filter(is_s, recv) + filter(is_s, sent),
                       0.)

        # Aggregate communication weights with destination
        w_dst = reduce(xPy1,
                       filter(is_d, recv) + filter(is_d, sent),
                       0.)

        # Reject transfer if it would result in less locality
        if w_src > w_dst:
            return False

        # Otherwise transfer may proceed
        return True

    ####################################################################
    def compute(self, object, p_src, p_dst):
        """A criterion allowing for local disruptions for more locality 
        """

        # Retrieve object communications
        comm = object.get_communicator()
        sent = comm.get_sent().items()
        recv = comm.get_received().items()

        # Retrieve ID of processor to which an object is assigned
        p_id = (lambda x: x.get_processor_id())

        # Test whether first component is source processor
        is_s = (lambda x: p_id(x[0]) == p_src.get_id())

        # Test whether first component is destination processor
        is_d = (lambda x: p_id(x[0]) == p_dst.get_id())

        # Add value with second components of a collection
        xPy1 = (lambda x, y: x + y[1])

        # Aggregate communication weights with source
        w_src = reduce(xPy1,
                       filter(is_s, recv) + filter(is_s, sent),
                       0.)

        # Aggregate communication weights with destination
        w_dst = reduce(xPy1,
                       filter(is_d, recv) + filter(is_d, sent),
                       0.)

        # Criterion assesses difference in local communications
        return w_dst - w_src

########################################################################
