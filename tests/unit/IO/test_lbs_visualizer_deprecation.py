import os
import logging
import unittest
import subprocess
from src.lbaf.IO.lbsVisualizer import Visualizer

class TestVizDeprecation(unittest.TestCase):
    """Test for lbsVisualizer's deprecation."""

    def test_lbs_visualizer_deprecation(self):
        try:
            visualizer = Visualizer(
                logger=logging.getLogger(),
                qoi_request=["this", "that", "the other thing"],
                continuous_object_qoi=False,
                phases=["phase 1", "phase 2"],
                grid_size=[0,0,1,1])
        except DeprecationWarning as e:
            assert str(e) == "LBAF's Visualizer has been deprecated and will be removed in a future release. Visualizations should be generated with DARMA/vt-tv."

if __name__ == "__main__":
    unittest.main()
