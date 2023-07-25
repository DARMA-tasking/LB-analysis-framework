import logging
import math
import random as rnd
from numpy import random
import unittest
from unittest.mock import patch

import lbaf.IO.lbsStatistics as lbsStatistics
from lbaf.IO.lbsStatistics import Statistics

def test_function(x):
    return x

class TestConfig(unittest.TestCase):
    # def setUp(self):
    #     self.logger = logging.getLogger()

    #     # Initialize statistics (currently nonsense)
    #     n=1
    #     mini=0.0
    #     mean=2.5
    #     maxi=5.0
    #     var=3.0
    #     g1=1.0
    #     g2=1.0

    #     # Manually store primary and derived statistics
    #     self.expected_primary_statistics = {
    #         "cardinality": n,
    #         "minimum": mini,
    #         "average": mean,
    #         "maximum": maxi,
    #         "variance": var,
    #         "skewness": g1,
    #         "kurtosis": g2}
    #     self.expected_derived_statistics = {
    #         "sum": n * mean,
    #         "imbalance":  maxi / mean - 1.0,
    #         "standard deviation": math.sqrt(var),
    #         "kurtosis excess": g2 - 3.0}

    #     # Create instance of Statistics class
    #     self.statistics = Statistics(
    #         n,
    #         mini,
    #         mean,
    #         maxi,
    #         var,
    #         g1,
    #         g2)

    # def test_lbs_stats_initialization(self):
    #     self.assertEqual(self.statistics.get_minimum(), self.mini)
    #     self.assertEqual(self.statistics.get_maximum(), self.maxi)
    #     self.assertEqual(self.statistics.get_average(), self.mean)
    #     self.assertAlmostEqual(self.statistics.get_variance(), self.var)
    #     self.assertAlmostEqual(self.statistics.get_skewness(), self.g1)
    #     self.assertAlmostEqual(self.statistics.get_kurtosis(), self.g2)

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
        expected_kurtosis = -1.2

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

    # def test_lbs_stats_compute_all_reachable_arrangements(self):

    # def test_lbs_stats_recursively_compute_transitions(self):

if __name__ == "__main__":
    unittest.main()
