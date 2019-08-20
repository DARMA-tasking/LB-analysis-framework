########################################################################
from lbsCriterionBase import CriterionBase

########################################################################
class ModifiedGrapevineCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6
    """

    ####################################################################
    def __init__(self, processors, edges, _):
        """Class constructor:
        processors: set of processors (lbsProcessor.Processor instances)
        edges: dictionary of edges (frozensets)
        _: no parameters dictionary needed for this criterion
        """

        # Call superclass init
        super(ModifiedGrapevineCriterion, self).__init__(processors, edges)
        print("[ModifiedGrapevineCriterion] Instantiated concrete criterion")
        
    ####################################################################
    def compute(self, object, p_src, p_dst):
        """Modified Grapevine criterion based on L1 norm of loads
        """

        # Criterion only uses object and processor loads
        return p_src.get_load() - (p_dst.get_load() + object.get_time())

########################################################################
