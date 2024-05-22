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

    def test_lbs_visualizer_config(self):
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "conf_wrong_visualization.yml")
        pipes = subprocess.Popen(["python", "src/lbaf", "-c", config_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_err = pipes.communicate()[1].decode("utf-8")
        assert "Visualization enabled but vttv not found. No visualization will be generated." in std_err

if __name__ == "__main__":
    unittest.main()
