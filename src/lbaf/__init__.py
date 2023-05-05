"""LBAF entry point"""

import os
import sys


# LBAF Version
__version__ = "0.1.0rc1"

from lbaf.Applications.LBAF_app import Application as LBAF_Application

def run():
    """Run an LBAF Application"""
    LBAF_Application().run()

if __name__ == "__main__":
    run()
