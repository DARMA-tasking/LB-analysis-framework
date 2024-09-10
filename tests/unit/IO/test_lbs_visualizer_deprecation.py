import os
import logging
import unittest
import subprocess
import importlib
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
        vttv = importlib.util.find_spec('vttv')
        if vttv is None:
            assert "Visualization enabled but vt-tv module not found." in std_err
        else:
            assert "Visualization enabled but vt-tv module not found." not in std_err
        assert pipes.returncode != 0 # error because missing json parameters required to run vt tv

if __name__ == "__main__":
    unittest.main()
