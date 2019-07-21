########################################################################
from lbsCriterionBase import CriterionBase

########################################################################
class ModifiedGrapevineCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6
    """

    ####################################################################
    def __init__(self, l, _):
        """Class constructor:
        l: list of processors
        _: no parameters needed
        """

        # Call superclass init
        super(ModifiedGrapevineCriterion, self).__init__(l)
        print("[ModifiedGrapevineCriterion] Instantiated concrete criterion")
        
    ####################################################################
    def is_satisfied(self, object, p_src, p_dst):
        """Original Grapevine criterion based on L1 norm of loads
        """

        # Criterion only uses object and processor loads
        return object.get_time() < p_src.get_load() - p_dst.get_load()

########################################################################
