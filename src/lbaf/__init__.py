"""LBAF entry point"""

import os
import sys


__version__ = "0.1.0rc1"
"""lbaf module version"""

PROJECT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../../")
"""project path (with data, config, tests)"""

from lbaf.Applications.LBAF_app import Application as LBAF_Application # pylint:disable=C0413


def run():
    """Run an LBAF Application"""
    LBAF_Application().run()

if __name__ == "__main__":
    run()
