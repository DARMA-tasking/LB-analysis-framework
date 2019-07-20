########################################################################
lbsCriterionBase_module_aliases = {}
for m in [
    "abc"
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsCriterionBase_module_aliases:
            globals()[lbsCriterionBase_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Model import lbsProcessor, lbsObject

########################################################################
class CriterionBase:
    __metaclass__ = abc.ABCMeta
    """An abstract base class of optimization criteria for LBS execution
    """

    ####################################################################
    def __init__(self, l, p=None):
        """Class constructor:
        l: set of processors
        p: optional parameters dictionary
        """

        # If no list of processors was was provided, do not do anything
        if not isinstance(l, set):
            print("** ERROR: Could not create a LBS criterion without a set of processors")
            return

        # Assert that all members of said list are indeed processor instances
        n_p = len(l)
        if n_p != len(
            filter(lambda x: isinstance(x, lbsProcessor.Processor), l)):
            print("** ERROR: Could not create a LBS criterion without a set of processors")
            return
            
        # Assign list of processors to criterion
        self.processors = l
        print("[CriterionBase] Assigned {} processors to base criterion".format(
            n_p))

    ####################################################################
    @abc.abstractmethod
    def is_satisfied(self, object, proc_src, proc_dst):
        """Tell whether object passes transfer criterion or not
        """

        # Must be implemented by concrete subclass
        pass
    
########################################################################
