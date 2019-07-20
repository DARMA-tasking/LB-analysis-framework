########################################################################
lbsGrapevineCriterion_module_aliases = {}
for m in [
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsGrapevineCriterion_module_aliases:
            globals()[lbsGrapevineCriterion_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from lbsCriterionBase import CriterionBase

########################################################################
class GrapevineCriterion(CriterionBase):
    """A concrete class for the original Grapevine criterion
    """

    ####################################################################
    def __init__(self, l, p):
        """Class constructor:
        l: list of processors
        p: parameters dictionary:
            average_load: average load across all processors
        v: verbose mode True/False
        """

        # Call superclass init
        super(GrapevineCriterion, self).__init__(l, p)

        # Keep track of average load across all processors
        key = "average_load"
        ave_load =  p.get(key)
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

########################################################################
