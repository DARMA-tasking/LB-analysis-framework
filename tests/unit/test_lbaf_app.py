import unittest

from lbaf.Applications.LBAF_app import LBAFApplication

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
                "offline_LB_compatible": False
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
