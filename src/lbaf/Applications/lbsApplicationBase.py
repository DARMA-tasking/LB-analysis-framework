import abc
import argparse
import sys

from lbaf.Utils.logger import get_logger, Logger
from lbaf.Utils.io import ask

class Arguments:
    """Wraps arguments dictionary in an object"""
    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)

class ApplicationBase:
    """Base class that represent an application for the lbaf module"""

    __metaclass__ = abc.ABCMeta

    _logger: Logger

    def __init__(self, interactive: bool = True, logger: Logger = get_logger()):
        """Initialize a new application instance.

        :param interactive: set True to enable the interactive mode.
          In that mode arguments values are collected interactively with prompts
        """
        parser = self.init_arguments()
        parser.add_argument('--no-interaction', type=None, nargs='*')
        if '--no-interaction' not in sys.argv and "-h" not in sys.argv and interactive:
            # if interactive
            args = {}
            for action in parser._actions:
                if action.dest != 'help':
                    args[action.dest] = ask(action.help, action.type, action.default, action.required)
            self._args = Arguments(args)
        else:
            # if help requested or no interactive way
            self._args = Arguments(parser.parse_args().__dict__)

        self._logger = logger

    def init_arguments(self) -> argparse.ArgumentParser:
        """Parse arguments. By default arguments supportes are -h (help) and --no-interaction (disable interactive mode if enabled)"""
        return argparse.ArgumentParser()

    def run(self):
        """Run the application"""
        raise NotImplementedError("This method must be overriden by child classes")
