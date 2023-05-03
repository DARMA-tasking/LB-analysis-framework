"""LBAF entry point"""#pylint:disable=C0103

import os
import sys


# LBAF Version
__version__ = "0.1.0rc1"

# LBAF Editable
__editable__ = True
for path_item in sys.path:
    egg_link = os.path.join(path_item, 'lbaf.egg-link')
    if os.path.isfile(egg_link):
        __editable__ = False

from lbaf.Applications.LBAF import Application as LBAF_Application # pylint:disable=C0413

def run():
    """Run an LBAF Application"""
    LBAF_Application().run()

if __name__ == "__main__":
    run()
