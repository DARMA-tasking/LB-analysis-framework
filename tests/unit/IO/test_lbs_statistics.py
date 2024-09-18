#
#@HEADER
###############################################################################
#
#                            test_lbs_statistics.py
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
import logging
import math
import random as rnd
import numpy as np
from numpy import random
from scipy import stats
import unittest

import lbaf.IO.lbsStatistics as lbsStatistics
from src.lbaf.IO.lbsStatistics import Statistics


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()

    def test_lbs_stats_compute_function_statistics(self):

        # Test with empty population and identity function
        empty_pop = []
        empty_result = lbsStatistics.compute_function_statistics(empty_pop, identity_function)

        # Assert the returned statistics match the expected values (nan)
        self.assertAlmostEqual(math.isnan(empty_result.get_minimum()), True)
        self.assertAlmostEqual(math.isnan(empty_result.get_maximum()), True)
        self.assertAlmostEqual(math.isnan(empty_result.get_average()), True)
        self.assertAlmostEqual(math.isnan(empty_result.get_variance()), True)
        self.assertAlmostEqual(math.isnan(empty_result.get_skewness()), True)
        self.assertAlmostEqual(math.isnan(empty_result.get_kurtosis()), True)

        # Test with a sample population and three different functions
        sample_pop_arr = random.normal(loc=5, scale=1.0, size=100)
        sample_pop = sample_pop_arr.tolist()

        # Get lists of output
        identity_output = identity_function(sample_pop)
        polynomial_output = polynomial_function(sample_pop)
        exponential_output = exponential_function(sample_pop)

        # Get results from lbsStatistics
        lbsStats_id = lbsStatistics.compute_function_statistics(sample_pop, id_test)
        lbsStats_poly = lbsStatistics.compute_function_statistics(sample_pop, poly_test)
        lbsStats_exp = lbsStatistics.compute_function_statistics(sample_pop, exp_test)

        # TESTING IDENTITY FUNCTION
        # Expected statistics based on the identity_output
        expected_min = min(identity_output)
        expected_max = max(identity_output)
        expected_average = sum(identity_output) / len(identity_output)
        expected_variance = sum((x - expected_average) ** 2 for x in identity_output) / len(identity_output)
        expected_skewness = stats.skew(identity_output)
        expected_kurtosis = stats.kurtosis(identity_output, fisher=False) # fisher=False uses Pearson's definition (normal ==> 3.0)

        # Expected derived statistics based on the identity_output
        expected_sum = sum(identity_output)
        expected_imbalance = max(identity_output) / (sum(identity_output) / len(identity_output)) - 1.0
        expected_standard_deviation = math.sqrt(expected_variance)
        expected_kurtosis_excess = expected_kurtosis - 3.0

        # # Assert the returned statistics match the expected values
        self.assertAlmostEqual(lbsStats_id.get_minimum(), expected_min)
        self.assertAlmostEqual(lbsStats_id.get_maximum(), expected_max)
        self.assertAlmostEqual(lbsStats_id.get_average(), expected_average)
        self.assertAlmostEqual(lbsStats_id.get_variance(), expected_variance)
        self.assertAlmostEqual(lbsStats_id.get_skewness(), expected_skewness)
        self.assertAlmostEqual(lbsStats_id.get_kurtosis(), expected_kurtosis)

        # Assert the returned statistics match the expected values for derived statistics
        self.assertAlmostEqual(lbsStats_id.get_sum(), expected_sum)
        self.assertAlmostEqual(lbsStats_id.get_imbalance(), expected_imbalance)
        self.assertAlmostEqual(lbsStats_id.get_standard_deviation(), expected_standard_deviation)
        self.assertAlmostEqual(lbsStats_id.get_kurtosis_excess(), expected_kurtosis_excess)

        # TESTING POLYNOMIAL FUNCTION
        # Expected statistics based on the polynomial_output
        expected_min = min(polynomial_output)
        expected_max = max(polynomial_output)
        expected_average = sum(polynomial_output) / len(polynomial_output)
        expected_variance = sum((x - expected_average) ** 2 for x in polynomial_output) / len(polynomial_output)
        expected_skewness = stats.skew(polynomial_output)
        expected_kurtosis = stats.kurtosis(polynomial_output, fisher=False)

        # Expected derived statistics based on the polynomial_output
        expected_sum = sum(polynomial_output)
        expected_imbalance = max(polynomial_output) / (sum(polynomial_output) / len(polynomial_output)) - 1.0
        expected_standard_deviation = math.sqrt(expected_variance)
        expected_kurtosis_excess = expected_kurtosis - 3.0

        # Assert the returned statistics match the expected values
        self.assertAlmostEqual(lbsStats_poly.get_minimum(), expected_min)
        self.assertAlmostEqual(lbsStats_poly.get_maximum(), expected_max)
        self.assertAlmostEqual(lbsStats_poly.get_average(), expected_average)
        self.assertAlmostEqual(lbsStats_poly.get_variance(), expected_variance)
        self.assertAlmostEqual(lbsStats_poly.get_skewness(), expected_skewness)
        self.assertAlmostEqual(lbsStats_poly.get_kurtosis(), expected_kurtosis)

        # Assert the returned statistics match the expected values for derived statistics
        self.assertAlmostEqual(lbsStats_poly.get_sum(), expected_sum)
        self.assertAlmostEqual(lbsStats_poly.get_imbalance(), expected_imbalance)
        self.assertAlmostEqual(lbsStats_poly.get_standard_deviation(), expected_standard_deviation)
        self.assertAlmostEqual(lbsStats_poly.get_kurtosis_excess(), expected_kurtosis_excess)

        # TESTING EXPONENTIAL FUNCTION
        # Expected statistics based on the exponential_output
        expected_min = min(exponential_output)
        expected_max = max(exponential_output)
        expected_average = sum(exponential_output) / len(exponential_output)
        expected_variance = sum((x - expected_average) ** 2 for x in exponential_output) / len(exponential_output)
        expected_skewness = stats.skew(exponential_output)
        expected_kurtosis = stats.kurtosis(exponential_output,fisher=False)

        # Expected derived statistics based on the exponential_output
        expected_sum = sum(exponential_output)
        expected_imbalance = max(exponential_output) / (sum(exponential_output) / len(exponential_output)) - 1.0
        expected_standard_deviation = math.sqrt(expected_variance)
        expected_kurtosis_excess = expected_kurtosis - 3.0

        # Assert the returned statistics match the expected values
        self.assertAlmostEqual(lbsStats_exp.get_minimum(), expected_min)
        self.assertAlmostEqual(lbsStats_exp.get_maximum(), expected_max)
        self.assertAlmostEqual(lbsStats_exp.get_average(), expected_average)
        self.assertAlmostEqual(lbsStats_exp.get_variance(), expected_variance)
        self.assertAlmostEqual(lbsStats_exp.get_skewness(), expected_skewness)
        self.assertAlmostEqual(lbsStats_exp.get_kurtosis(), expected_kurtosis)

        # Assert the returned statistics match the expected values for derived statistics
        self.assertAlmostEqual(lbsStats_exp.get_sum(), expected_sum)
        self.assertAlmostEqual(lbsStats_exp.get_imbalance(), expected_imbalance)
        self.assertAlmostEqual(lbsStats_exp.get_standard_deviation(), expected_standard_deviation)
        self.assertAlmostEqual(lbsStats_exp.get_kurtosis_excess(), expected_kurtosis_excess)

def id_test(x):
    return x

def poly_test(x):
    return 4 + x**2

def exp_test(x):
    return np.exp(x)

def identity_function(population):
    y = []
    for x in population:
        y.append(id_test(x))
    return y

def polynomial_function(population):
    y = []
    for x in population:
        y.append(poly_test(x))
    return y

def exponential_function(population):
    y = []
    for x in population:
        y.append(exp_test(x))
    return y

if __name__ == "__main__":
    unittest.main()
