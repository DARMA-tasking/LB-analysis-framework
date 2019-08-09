########################################################################
from lbsCriterionBase import CriterionBase

########################################################################
class GrapevineCriterion(CriterionBase):
    """A concrete class for the original Grapevine criterion
    """

    ####################################################################
    def __init__(self, processors, edges, parameters):
        """Class constructor:
        processors: set of processors (lbsProcessor.Processor instances)
        edges: dictionary of edges (frozensets)
        parameters: optional parameters dictionary
            average_load: average load across all processors
        """

        # Call superclass init
        super(GrapevineCriterion, self).__init__(processors, edges, parameters)

        # Keep track of average load across all processors
        key = "average_load"
        ave_load =  parameters.get(key)
        if ave_load:
            self.average_load = ave_load
            print("[GrapevineCriterion] Instantiated concrete criterion with average load: {}".format(
            ave_load))
        else:
            print("** ERROR: cannot instantiate criterion without {} parameter".format(
                key))

    ####################################################################
    def is_satisfied(self, object, _, p_dst):
        """Original Grapevine criterion based on Linfinity norm of loads
        """

        # Criterion only uses object and processor loads
        return p_dst.get_load() + object.get_time() < self.average_load

    ####################################################################
    def compute(self, object, _, p_dst):
        """Original Grapevine criterion based on Linfinity norm of loads
        """

        # Criterion only uses object and processor loads
        return self.average_load - (p_dst.get_load() + object.get_time())

########################################################################
