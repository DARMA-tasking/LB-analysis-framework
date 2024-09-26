#
#@HEADER
###############################################################################
#
#                      test_lbs_visualizer_deprecation.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
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
