########################################################################
lbsModifiedGrapevineCriterion_module_aliases = {}
for m in [
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsModifiedGrapevineCriterion_module_aliases:
            globals()[lbsModifiedGrapevineCriterion_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from lbsCriterionBase import CriterionBase

########################################################################
class ModifiedGrapevineCriterion(CriterionBase):
    """A concrete class for the Grapevine criterion modified in line 6
    """

    ####################################################################
    def __init__(self, l):
        """Class constructor:
        l: list of processors
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
