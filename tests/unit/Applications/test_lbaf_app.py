#
#@HEADER
###############################################################################
#
#                               test_lbaf_app.py
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
import unittest

from src.lbaf.Applications.LBAF_app import LBAFApplication

class TestLBAFApplication(unittest.TestCase):
    """Tests for LBAFApplication"""

    def setUp(self):
        pass

    def _global_conf(self) -> dict:
        """Sample global configuration subset"""
        return {
            "algorithm": {
                "name": "BruteForce",
                "parameters": {
                    "transfer_strategy": "Recursive",
                }
            },
            "output_dir": "../output",
            "write_JSON": {
                "compressed": False,
                "suffix": "json",
                "communications": True,
                "offline_lb_compatible": False
            }
        }

    def _local_conf(self) -> dict:
        """Sample local configuration subset"""
        return {
            "from_data": {
                "data_stem": "../data/synthetic_lb_data/data",
                "phase_ids": [0]
            },
            "check_schema": False,
            "algorithm": {
                "name": "InformAndTransfer",
                "parameters": {
                    "fanout": 3
                }
            }
        }

    def test_configuration_merge(self):
        """Test that 2 dictionaries generates a single dictionay as expected.

        The following are tested:
        - Keys defined only in global configuration
        - Keys defined only in local configuration
        - Keys that must be overriden by the local configuration
        """

        app = LBAFApplication()
        data = {}
        # Inject some global configuration
        data = app._LBAFApplication__merge(self._global_conf(), data)
        global_conf = self._global_conf()
        local_conf = self._local_conf()
        # Test merge results in a copy of the global configuration
        self.assertDictEqual(data, global_conf)

        # Inject some local configuration
        data = app._LBAFApplication__merge(local_conf, data)
        # Keys defined only in global config must still be there
        self.assertIsNotNone(data.get("write_JSON", None))
        self.assertDictEqual(data.get("write_JSON"), global_conf.get("write_JSON")) # dict should also be the same
        self.assertEqual(data.get("algorithm", {}).get("parameters", {}).get("transfer_strategy"),"Recursive")
        self.assertEqual(data.get("output_dir", {}),"../output")
        # Keys defined only in local config must also be there
        self.assertIsNotNone(data.get("from_data", None))
        # Keys that must be overriden by the local configuration
        self.assertEqual(data.get("algorithm", {}).get("name"), "InformAndTransfer")
        self.assertEqual(data.get("algorithm", {}).get("parameters", {}).get("fanout"), 3)

if __name__ == "__main__":
    unittest.main()
