########################################################################
lbsStatistics_module_aliases = {
    "random": "rnd",
    }
for m in [
    "random",
    "math",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsStatistics_module_aliases:
            globals()[lbsStatistics_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

########################################################################
def initialize():

    # Seed pseudo-random number generator
    rnd.seed()

########################################################################
def sampler(distribution_name, parameters):
    """Return a pseudo-random number generator based of requested type
    """

    # Uniform U(a,b) distribution
    if distribution_name.lower() == "uniform":
        if len(parameters) < 2:
            print "** ERROR: not enough parameters in {} for {} distribution.".format(
                parameters,
                distribution_name)
            return None

        # Return uniform distribution over given interval
        return lambda : rnd.uniform(parameters[0], parameters[1]), .5 * sum(parameters)

    # Log-normal distribution with given mean and variance
    if distribution_name.lower() == "lognormal":
        if len(parameters) < 2:
            print "** ERROR: not enough parameters in {} for {} distribution.".format(
                parameters,
                distribution_name)
            return None

        if r == 0:
            print "** ERROR: r={} should not be zero.".format(r)
            return None

        # Determine parameters of log-normal distribution
        m2 = parameters[0] * parameters[0]
        v = parameters[1]
        r = math.sqrt(m2 + v)
        mu = math.log(m2 / r)
        sigma = math.sqrt(math.log(r * r / m2))

        # Return log-normal distribution with given mean and variance
        return lambda : rnd.lognormvariate(mu, sigma), parameters[0]

    # Unsupported distribution type
    else:
        print "** ERROR: {} distribution is not supported."
        return None, None

########################################################################
def inverse_transform_sample(values, cmf):
    """Sample from distribution defined by cumulative mass function
    This is a.k.a. the Smirnov transform
    values: set of increasing values in R
    cmf: corresponding CMF values (listst must have identical lengths)
    """

    # Generate number from pseudo-random dsitribution U([0;1])
    u = rnd.random()

    # Look for when u is first encountered in CMF
    for i, x in enumerate(cmf):
        if not x < u:
            # Return sample point
            return values[i]

########################################################################
def compute_function_mean(population, fct):
    """Compute mean of a function over a population
    """

    # Bail out early if population is empty
    n = len(population)
    if not n:
        return None

    # Return arithmetic mean is not zero
    return sum([fct(x) for x in population]) / n

########################################################################
def compute_function_statistics(population, fct):
    """Compute descriptive statistics of a function over a population
    """

    # Bail out early if population is empty
    if not len(population):
        return 0, None, None, None, None

    # Initialize statistics
    n = 0
    f_min = float('inf')
    f_max = - float('inf')
    f_ave = 0.
    f_ag2 = 0.
    f_ag3 = 0.
    f_ag4 = 0.

    # Stream population and to compute function statistics
    for x in population:
        # Compute image by function
        y = fct(x)

        # Update cardinality
        n += 1

        # Update minimum
        if y < f_min:
            f_min = y

        # Update maximum
        if y > f_max:
            f_max = y

        # Compute difference to mean and its inverse
        d = y - f_ave
        A = d / n

        # Update mean and difference to updated mean
        f_ave += A
        B = y - f_ave

        # Update aggregates in this order as previous values required
        r = n - 1
        f_ag4 += A * (A * A * d * r * (n * (n - 3) + 3) + 6 * A * f_ag2 - 4 * f_ag3)
        f_ag3 += A * (B * d * (n - 2) - 3 * f_ag2)
        f_ag2 += d * B

    # Return cardinality, minimum, mean, maximum, variance, skewness, kurtosis excess
    var = f_ag2 / n
    nvar = n * var
    return n, f_min, f_ave, f_max, var, f_ag3 / (nvar * math.sqrt(var)), f_ag4 / (nvar * var) 

########################################################################
