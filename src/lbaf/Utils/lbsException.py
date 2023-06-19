"""
This module defines exception related classes and functions.

- TerseError: Exception class for errors where the traceback must be hidden
- exc_handler: Exception handler for hiding traceback of errors of type TerseError. To register on application startup.

"""
import traceback

import os
import sys

from .lbsColors import red


class TerseError(Exception):
    """Represent terse errors (no display of the stack trace).

    Note that the display support of such errors is provided by the following handler : lbsException.exc_handler
    To register this handler please call `sys.excepthook = lbsException.exc_handler` at application startup
    """


def exc_handler(type_, value, traceback_):
    """Exception handler that brings support of display of lbsException.TersError
    To register this handler please call `sys.excepthook = lbsException.exc_handler` at application startup."""
    filename, _line_num, _func_name, _text = traceback.extract_tb(traceback_)[-1]
    modulename = os.path.basename(filename).replace('.py', '')
    if type_ == TerseError:
        # custom display for TerseError
        print(red(f"[{modulename}] ") + value.__str__())
    else:
        # or default system handler
        sys.__excepthook__(type_, value, traceback)
