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
            print "** ERROR: [Statistics] not enough parameters in {} for {} distribution.".format(
                parameters,
                distribution_name)
            return None

        # Return uniform distribution over given interval
        return lambda : rnd.uniform(parameters[0], parameters[1]), .5 * sum(parameters)

    # Log-normal distribution with given mean and variance
    if distribution_name.lower() == "lognormal":
        if len(parameters) < 2:
            print "** ERROR: [Statistics] not enough parameters in {} for {} distribution.".format(
                parameters,
                distribution_name)
            return None

        if r == 0:
            print "** ERROR: [Statistics] r={} should not be zero.".format(r)
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
        print "** ERROR: [Statistics] {} distribution is not supported."
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

    # Compute variance
    f_var = f_ag2 / n
    
    # Compute skewness and kurtosis depending on variance
    if f_var > 0.:
        nvar = n * f_var
        f_g1, f_g2 = f_ag3 / (nvar * math.sqrt(f_var)), f_ag4 / (nvar * f_var)
    else:
        f_g1, f_g2 = float('nan'), float('nan')

    # Return cardinality, minimum, mean, maximum, variance, skewness, kurtosis
    return n, f_min, f_ave, f_max, f_var, f_g1, f_g2

########################################################################
def print_function_statistics(values, function, var_name, verb=False):
    """Compute detailed statistics of function values and print to standard output
    """

    # Compute statistics
    n, f_min, f_ave, f_max, f_var, f_g1, f_g2 = compute_function_statistics(
        values,
        function)

    # Always print summary but use function descriptor only in verbose case
    if verb:
        print "[Statistics] Computing descriptive statistics of {} (f):".format(
            var_name,
            n)
    else:
        print "[Statistics] Computing descriptive statistics of {}:".format(
            var_name,
            n)

    # Print detailed load information if requested
    if verb:
        for v in values:
            print "\t f({}) = {}".format(
                v.get_id(),
                function(v))

    # Print summary
    print "\t cardinality = {:.6g}  sum = {:.6g}".format(
        n,
        n * f_ave)
    print "\t minimum = {:.6g}  maximum = {:.6g}".format(
        f_min,
        f_max)
    print "\t mean = {:.6g}  standard deviation = {:.6g}".format(
        f_ave,
        math.sqrt(f_var))
    print "\t skewness = {:.6g}  kurtosis excess = {:.6g}".format(
        f_g1,
        f_g2 - 3)

    # Return cardinality, minimum, mean, maximum, variance, skewness, kurtosis
    return n, f_min, f_ave, f_max, f_var, f_g1, f_g2

########################################################################
