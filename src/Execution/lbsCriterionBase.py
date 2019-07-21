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
    def __init__(self, processors, edges, parameters=None):
        """Class constructor:
        processors: set of processors (lbsProcessor.Processor instances)
        edges: dictionary of edges (frozensets)
        parameters: optional parameters dictionary
        """

        # If no list of processors was was provided, do not do anything
        if not isinstance(processors, set):
            print("** ERROR: Could not create a LBS criterion without a set of processors")
            return

        # Assert that all members of said list are indeed processor instances
        n_p = len(processors)
        if n_p != len(
            filter(lambda x: isinstance(x, lbsProcessor.Processor), processors)):
            print("** ERROR: Could not create a LBS criterion without a set of Processor instances")
            return
            
        # If no dictionary of edges was was provided, do not do anything
        if not isinstance(edges, dict):
            print("** ERROR: Could not create a LBS criterion without a dictionary of edges")
            return

        # Assert that all members of said dictionary are indeed frozen sets
        n_e = len(edges)
        if n_e != len(
            filter(lambda x: isinstance(x, frozenset), edges)):
            print("** ERROR: Could not create a LBS criterion without a dictionary of frozen sets")
            return

        # Criterion keeps internal references to processors and edges
        self.processors = processors
        self.edges = edges
        print("[CriterionBase] Assigned {} processors and {} edges to base criterion".format(
            n_p,
            n_e))

    ####################################################################
    @abc.abstractmethod
    def is_satisfied(self, object, proc_src, proc_dst):
        """Tell whether object passes transfer criterion or not
        """

        # Must be implemented by concrete subclass
        pass
    
########################################################################
