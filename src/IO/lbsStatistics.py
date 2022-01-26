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
from logging import Logger
import math
import random as rnd

import numpy as np

from src.Utils.logger import CLRS

# Setup colors
grn = CLRS.get('green')
red = CLRS.get('red')
ylw = CLRS.get('yellow')


def initialize():
    # Seed pseudo-random number generators
    rnd.seed(820)
    np.random.seed(820)


def error_out(distribution_name, parameters, logger: Logger = None):
    logger.error(red(f"not enough parameters in {parameters} for {distribution_name} distribution."))
    return None


def sampler(distribution_name, parameters, logger: Logger = None):
    """Return a pseudo-random number generator based of requested type
    """

    # Uniform U(a,b) distribution
    if distribution_name.lower() == "uniform":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters, logger=logger)

        # Return uniform distribution over given interval
        return lambda: rnd.uniform(*parameters), "U[{};{}]".format(*parameters)

    # Binomial B(n,p) distribution
    elif distribution_name.lower() == "binomial":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters, logger=logger)

        # Return binomial distribution with given number of Bernoulli trials
        return lambda: np.random.binomial(*parameters), "B[{};{}]".format(*parameters)

    # Log-normal distribution with given mean and variance
    elif distribution_name.lower() == "lognormal":
        # 2 parameters are needed
        if len(parameters) < 2:
            return error_out(distribution_name, parameters, logger=logger)

        # Determine parameters of log-normal distribution
        m2 = parameters[0] * parameters[0]
        v = parameters[1]
        r = math.sqrt(m2 + v)
        if r == 0:
            logger.error(red(f"r={r} should not be zero."))
            return None, None
        mu = math.log(m2 / r)
        sigma = math.sqrt(math.log(r * r / m2))

        # Return log-normal distribution with given mean and variance
        return lambda : rnd.lognormvariate(mu, sigma), "LogN({:.6g};{:.6g})".format(
            mu,
            sigma)

    # Unsupported distribution type
    else:
        logger.error(red(f"{distribution_name} distribution is not supported."))
        return None, None


def inverse_transform_sample(cmf):
    """Sample from distribution defined by cumulative mass function
    This is a.k.a. the Smirnov transform
    """

    # Generate number from pseudo-random dsitribution U([0;1])
    u = rnd.random()

    # Look for when u is first encountered in CMF
    for k, v in cmf.items():
        if not v < u:
            # Return sample point
            return k


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

    # Compute imbalance
    f_imb = f_max / f_ave - 1. if f_ave > 0. else nan

    # Return cardinality, minimum, mean, maximum, variance, skewness, kurtosis, imbalance
    return n, f_min, f_ave, f_max, f_var, f_g1, f_g2, f_imb


def print_function_statistics(values, function, var_name, logger: Logger = None, file: str = None):
    """Compute and report descriptive statistics of function values
    """
    # Compute statistics
    logger.info(grn(f"Descriptive statistics of {var_name}:"))
    n, f_min, f_ave, f_max, f_var, f_g1, f_g2, f_imb = compute_function_statistics(
        values,
        function)

    # Save imbalance for testing purposes
    if var_name == 'final rank loads' and file is not None:
        with open(file, 'w') as imbalance_file:
            imbalance_file.write(f"{f_imb}")

    # Print detailed load information if requested
    for i, v in enumerate(values):
        logger.debug(ylw(f"\t{i}: {function(v)}"))

    # Print summary
    logger.info(grn(f"\tcardinality: {n:.6g}  sum: {n * f_ave:.6g}  imbalance: {f_imb:.6g}"))
    logger.info(grn(f"\tminimum: {f_min:.6g}  mean: {f_ave:.6g}  maximum: {f_max:.6g}"))
    logger.info(grn(f"\tstandard deviation: {math.sqrt(f_var):.6g}  variance: {f_var:.6g}"))
    logger.info(grn(f"\tskewness: {f_g1:.6g}  kurtosis excess: {f_g2 - 3.:.6g}"))

    # Return cardinality, minimum, mean, maximum, variance, skewness, kurtosis
    return n, f_min, f_ave, f_max, f_var, f_g1, f_g2, f_imb


def print_subset_statistics(subset_name, subset_size, set_name, set_size, logger: Logger = None):
    """Compute and report descriptive statistics of subset vs. full set
    """

    # Print summary
    ss = f"{100. * subset_size / set_size:.3g}" if set_size else ''
    logger.info(grn(f"{subset_name}: {subset_size:.6g} amongst {set_name}: {set_size:.6g} ({ss}%)"))


        
        
