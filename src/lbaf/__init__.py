"""LBAF entry point"""#pylint:disable=C0103

# LBAF Version
__version__ = "0.1.0rc1"

from lbaf.Applications.LBAF import Application as LBAF_Application

def run():
    """Run an LBAF Application"""
    LBAF_Application().run()

if __name__ == "__main__":
    run()
