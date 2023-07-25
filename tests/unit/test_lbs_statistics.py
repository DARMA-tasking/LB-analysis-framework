import logging
import math
import random as rnd
from numpy import random
import unittest

import lbaf.IO.lbsStatistics as lbsStatistics
from lbaf.IO.lbsStatistics import Statistics


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger()

    def test_lbs_stats_compute_function_statistics(self):

        # Test with empty population
        empty_pop = []
        empty_result = lbsStatistics.compute_function_statistics(empty_pop, test_function)

        # Assert the returned statistics match the expected values (nan)
        self.assertEqual(math.isnan(empty_result.get_minimum()), True)
        self.assertEqual(math.isnan(empty_result.get_maximum()), True)
        self.assertEqual(math.isnan(empty_result.get_average()), True)
        self.assertEqual(math.isnan(empty_result.get_variance()), True)
        self.assertEqual(math.isnan(empty_result.get_skewness()), True)
        self.assertEqual(math.isnan(empty_result.get_kurtosis()), True)

        # Test with a population and simple function
        sample_pop = [1, 2, 3, 4, 5]
        result = lbsStatistics.compute_function_statistics(sample_pop, test_function)

        # Expected statistics based on the input population
        expected_min = 1
        expected_max = 5
        expected_average = sum(sample_pop) / len(sample_pop)
        expected_variance = sum((x - expected_average) ** 2 for x in sample_pop) / len(sample_pop)
        expected_skewness = 0
        expected_kurtosis = 1.7

        # Expected derived statistics based on the input population and computed primary statistics
        expected_sum = sum(sample_pop)
        expected_imbalance = max(sample_pop) / (sum(sample_pop) / len(sample_pop)) - 1.0
        expected_standard_deviation = math.sqrt(result.get_variance())
        expected_kurtosis_excess = result.get_kurtosis() - 3.0

        # Assert the returned statistics match the expected values
        self.assertEqual(result.get_minimum(), expected_min)
        self.assertEqual(result.get_maximum(), expected_max)
        self.assertEqual(result.get_average(), expected_average)
        self.assertAlmostEqual(result.get_variance(), expected_variance)
        self.assertAlmostEqual(result.get_skewness(), expected_skewness)
        self.assertAlmostEqual(result.get_kurtosis(), expected_kurtosis)

        # Assert the returned statistics match the expected values for derived statistics
        self.assertEqual(result.get_sum(), expected_sum)
        self.assertAlmostEqual(result.get_imbalance(), expected_imbalance)
        self.assertAlmostEqual(result.get_standard_deviation(), expected_standard_deviation)
        self.assertAlmostEqual(result.get_kurtosis_excess(), expected_kurtosis_excess)

def test_function(x):
    return x

if __name__ == "__main__":
    unittest.main()
