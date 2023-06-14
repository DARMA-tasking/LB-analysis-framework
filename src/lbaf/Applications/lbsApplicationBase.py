import abc
import argparse
from itertools import repeat
from os import linesep
import sys
from typing import Optional

from lbaf.Utils.logger import get_logger, Logger
from lbaf.Utils.cli import title, ask


class ApplicationBase:
    """Base class that represent an application for the lbaf module"""

    __metaclass__ = abc.ABCMeta

    _logger: Logger

    def __init__(self, logger: Logger = get_logger(), interactive: bool = True):
        """Initialize a new application instance.

        :param logger: the logger to use at the application level.
        """
        self._logger = logger
        self._args = argparse.Namespace()
        self.interactive = interactive
        print("Interactive Mode=" + ("True" if self.interactive is True else "False"))

    def init_argument_parser(self) -> argparse.ArgumentParser:
        """Defines the expected arguments for this application.

        Do not add the following arguments to the returned parser since these will be added internally:
        -h or --help: to display help)
        """
        return argparse.ArgumentParser()

    def parse_args(self, args: Optional[dict] = None):
        """Load application arguments.
        
        :param args: arguments to use or None to load from CLI
        :param interactive: set True to enable to ask user for argument values in CLI.
        """
        parser = self.init_argument_parser()
        print(parser._actions)
        print("----------------")
        parser.add_argument('--no-interaction', type=None, nargs='*', help='disable prompt')
        if args is not None:
            # if args given to this method call directly just fill Namespace
            for arg in args:
                if not hasattr(self._args, arg):
                    setattr(self._args, arg, None)
        else:
            if "--no-interaction" in sys.argv and self.interactive:
                self.interactive = False
                print("Interactive Mode disabled by --no-interaction")
            interactive = self.interactive

            help_requested = "-h" in sys.argv or "--help" in sys.argv
            if not help_requested:
                # check if any arg given consider that user do now want to use interactions
                for action in parser._actions:
                    if (
                        any(map(lambda v, action=action: v in action.option_strings and
                            action.dest != 'help' and action.dest != 'no_interaction', sys.argv))
                    ):
                        interactive = False
                if interactive:
                    # if interactive
                    title(type(self).__name__.replace('Application', '') + " Application")
                    for action in parser._actions:
                        if action.dest != 'help' and action.dest != 'no_interaction':
                            values = ask(
                                action.dest + linesep +
                                ''.join(list(repeat('-', len(action.dest)))) + linesep + action.help,
                                action.type, action.default, action.required, action.choices)
                            # call the action for potential values transformer
                            action(parser, self._args, values)
                else:
                    # if help requested or no interactive way
                    self._args = parser.parse_args()
            else:
                print(parser.format_help())
                raise SystemExit(1)
        return self

    @abc.abstractmethod
    def run(self, args: Optional[dict] = None) -> int:
        """Run the application.

        If args are required then this method must call the self.parse_args method.

        :param args: arguments to use or None to load from CLI
        :returns: return code. 0 if success.
        """
        raise NotImplementedError("Please implement the execution logic in child class")
