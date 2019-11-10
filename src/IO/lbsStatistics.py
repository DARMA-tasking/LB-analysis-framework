#
#@HEADER
###############################################################################
#
#                               lbsStatistics.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
########################################################################
lbsStatistics_module_aliases = {
    "random": "rnd",
    "numpy" : "np",
    }
for m in [
    "random",
    "math",
    "numpy",
    "bcolors",
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
        print("** ERROR: failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

########################################################################
def initialize():

    # Seed pseudo-random number generators
    rnd.seed(820)
    np.random.seed(820)

########################################################################
def error_out(distribution_name, parameters):

    print(bcolors.ERR
        + "*  ERROR: [Statistics] not enough parameters in {} for {} distribution.".format(
        parameters,
        distribution_name)
        + bcolors.END)
    return None

########################################################################
def sampler(distribution_name, parameters):
    """Return a pseudo-random number generator based of requested type
    """

    # Uniform U(a,b) distribution
    if distribution_name.lower() == "uniform":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters)

        # Return uniform distribution over given interval
        return lambda : rnd.uniform(*parameters), "U[{};{}]".format(
            *parameters)

    # Binomial B(n,p) distribution
    if distribution_name.lower() == "binomial":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters)

        # Return binomial distribution with given number of Bernoulli trials
        return lambda : np.random.binomial(*parameters), "B[{};{}]".format(
            *parameters)

    # Log-normal distribution with given mean and variance
    elif distribution_name.lower() == "lognormal":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters)

        # Determine parameters of log-normal distribution
        m2 = parameters[0] * parameters[0]
        v = parameters[1]
        r = math.sqrt(m2 + v)
        if r == 0:
            print(bcolors.ERR
                + "*  ERROR: [Statistics] r={} should not be zero.".format(r)
                + bcolors.END)
            return None, None
        mu = math.log(m2 / r)
        sigma = math.sqrt(math.log(r * r / m2))

        # Return log-normal distribution with given mean and variance
        return lambda : rnd.lognormvariate(mu, sigma), "LogN({:.6g};{:.6g})".format(
            mu,
            sigma)

    # Unsupported distribution type
    else:
        print(bcolors.ERR
            + "*  ERROR: "
            + bcolors.HEADER
            + "[Statistics] "
            + bcolors.END
            + "{} distribution is not supported."
            + bcolors.END)
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

    # Shorthand for NaN
    nan = float("nan")

    # Bail out early if population is empty
    if not len(population):
        return 0, nan, nan, nan, nan, nan, nan, nan

    # Initialize statistics
    n = 0
    f_min = float('inf')
    f_max = -float('inf')
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
        f_g1, f_g2 = nan, nan

    # Return cardinality, minimum, mean, maximum, variance, skewness, kurtosis, imbalance
    return n, f_min, f_ave, f_max, f_var, f_g1, f_g2, f_max / f_ave - 1.

########################################################################
def print_function_statistics(values, function, var_name, verb=False):
    """Compute and report descriptive statistics of function values
    """

    # Compute statistics
    print(bcolors.HEADER
        + "[Statistics] "
        + bcolors.END
        + "Descriptive statistics of {}:".format(var_name))
    n, f_min, f_ave, f_max, f_var, f_g1, f_g2, f_imb = compute_function_statistics(
        values,
        function)

    # Print detailed load information if requested
    if verb:
        for i, v in enumerate(values):
            print("\t{}: {}".format(
                i,
                function(v)))

    # Print summary
    print("\tcardinality: {:.6g}  sum: {:.6g}  imbalance: {:.6g}".format(
        n,
        n * f_ave,
        f_imb))
    print("\tminimum: {:.6g}  mean: {:.6g}  maximum: {:.6g}".format(
        f_min,
        f_ave,
        f_max))
    print("\tstandard deviation: {:.6g}  variance: {:.6g}".format(
        math.sqrt(f_var),
        f_var))
    print("\tskewness: {:.6g}  kurtosis excess: {:.6g}".format(
        f_g1,
        f_g2 - 3.))

    # Return cardinality, minimum, mean, maximum, variance, skewness, kurtosis
    return n, f_min, f_ave, f_max, f_var, f_g1, f_g2, f_imb

########################################################################
def print_subset_statistics(var_name, set_name, set_size, subset_name, subset_size):
    """Compute and report descriptive statistics of subset vs. full set
    """

    # Print summary
    print(bcolors.HEADER
        + "[Statistics] "
        + bcolors.END
        + "{}:".format(var_name))
    print("\t{}: {:.6g}  {}: {:.6g} {}".format(
        set_name,
        set_size,
        subset_name,
        subset_size,
        "({:.4g}%)".format(100. * subset_size / set_size) if set_size else ''))

########################################################################
