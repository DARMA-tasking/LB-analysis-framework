import abc
import argparse
import sys
from typing import Optional

from lbaf.Utils.logger import get_logger, Logger
from lbaf.Utils.io import ask

class Arguments:
    """Wraps arguments dictionary in an object"""   
    def __init__(self, args: Optional[dict] = None):
        if args is not None:
            for key, value in args.items():
                setattr(self, key, value)

class ApplicationBase:
    """Base class that represent an application for the lbaf module"""

    __metaclass__ = abc.ABCMeta

    _logger: Logger

    def __init__(self, logger: Logger = get_logger()):
        """Initialize a new application instance.

        :param logger: the logger to use at the application level.
        """
        self._args = Arguments()
        self._logger = logger

    def init_argument_parser(self) -> argparse.ArgumentParser:
        """Defines the expected arguments for this application.

        Do not add the following arguments to the returned parser since these will be added internally:
        -h or --help: to display help)
        --no-interaction: to disable interactive mode if enabled in initialization
        """
        return argparse.ArgumentParser()

    def parse_args(self, args: Optional[dict] = None, interactive: bool = True):
        """Load application arguments.

        :param args: arguments to use or None to load from CLI
        :param interactive: set True to enable to ask user for argument values in CLI.
        """
        parser = self.init_argument_parser()
        if args is not None:
            self._args = Arguments(args)
        else:
            parser.add_argument('--no-interaction', type=None, nargs='*')
            interactive = interactive and "--no-interaction" not in sys.argv
            help_requested = "-h" in sys.argv or "--help" in sys.argv
            if not help_requested:
                if interactive:
                    # if interactive
                    args = {}
                    for action in parser._actions:
                        if action.dest != 'help' and action.dest != 'no_interaction':
                            args[action.dest] = ask(action.help, action.type, action.default, action.required)
                    self._args = Arguments(args)
                else:
                    # if help requested or no interactive way
                    self._args = Arguments(parser.parse_args().__dict__)
            print(parser.format_help())
            exit()
        return self

    @abc.abstractmethod
    def run(self)-> int:
        """Run the application.

        If args are required then this method must call the self.parse_args method.

        :returns: return code. 0 if success.
        """
        raise NotImplementedError("Please implement the execution logic in child class")
