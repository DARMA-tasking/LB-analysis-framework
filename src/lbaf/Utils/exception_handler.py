import os

from .colors import red


def exc_handler(exception_type, exception, traceback):
    """ Exception handler for hiding traceback. """
    module_name = red(f"[{os.path.splitext(os.path.split(__file__)[-1])[0]}]")
    print(f"{module_name} {exception_type.__name__} {exception}")
