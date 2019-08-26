########################################################################
lbsCriterion_module_aliases = {}
for m in [
    "importlib",
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsCriterion_module_aliases:
            globals()[lbsCriterion_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("** ERROR: failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

########################################################################
class Criterion(object):
    """A helper factory to instantiate desired concrete criteria
    """

    ####################################################################
    @staticmethod
    def factory(criterion_idx, processors, edges, parameters=None):
        """Produce the necessary concrete criterion
        """

        # Ensure that criterion index is valid
        c_name = {
            0: "GrapevineCriterion",
            1: "ModifiedGrapevineCriterion",
            2: "StrictLocalizingCriterion",
            3: "RelaxedLocalizingCriterion",
            }.get(criterion_idx)
        if not c_name:
            print("** ERROR: unsupported criterion index: {}".format(
                criterion_idx))
            return None

        #Try to load corresponding module
        m_name = "Execution.lbs{}".format(c_name)
        try:
            module = importlib.import_module(m_name)
        except:
            print("** ERROR: could not load module `{}`".format(
                m_name))
            return None

        # Try to get concrete criterion class from module
        try:
            c_class = getattr(module, c_name)
        except:
            print("** ERROR: could not get class `{}` from module `{}`".format(
                c_name,
                m_name))
            return None
            
        # Instantiate and return object
        ret_object = c_class(processors, edges, parameters)
        print("[Criterion] Instantiated {} load transfer criterion".format(
            c_name))
        return ret_object

########################################################################
