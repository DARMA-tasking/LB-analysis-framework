import abc
import argparse
import sys
from typing import Optional

from .logger import get_logger, Logger
from .cli import title, ask


class RunnerBase:
    """Base class to run some logic with some arguments.

    Arguments will be set using one of the following methods:
    - Set directly using a dictionary
    - Set automatically by parsing CLI arguments
    - Ask user for values (if prompt is set to True).
    Note that prompt method will be disabled if any argument is detected in the command line.
    In that case we consider that the user want to set arguments inline with the command call

    :param logger: the logger to use at the application level.
    :param prompt: set True to prompt the user to enter values for all command arguments
    """

    __metaclass__ = abc.ABCMeta

    _logger: Logger

    def __init__(self, logger: Logger = get_logger(), prompt: bool = True):
        self._logger = logger
        self._args = argparse.Namespace()
        self.prompt = prompt

    def init_argument_parser(self) -> argparse.ArgumentParser:
        """Defines the expected arguments for this application.

        Do not add the following arguments to the returned parser since these will be added internally:
        -h or --help: to display help)
        """
        return argparse.ArgumentParser()

    def load_args(self, args: Optional[dict] = None):
        """Load application arguments.

        :param args: arguments to use. Set None to parse values from CLI.
        :returns: self
        """
        parser = self.init_argument_parser()
        parser.add_argument('--prompt', type=None, nargs='*',
            help='Prompt the user to enter values for all command arguments')
        if args is not None:
            # if args given to this method call directly just fill Namespace
            for arg in args:
                if not hasattr(self._args, arg):
                    setattr(self._args, arg, None)
        else:
            # check if help is requested then output and exit
            help_requested = "-h" in sys.argv or "--help" in sys.argv
            if help_requested:
                print(parser.format_help())
                raise SystemExit(1)

            # check if prompt is explicitly requested
            if "--prompt" in sys.argv:
                self.prompt = True
            for action in parser._actions:
                if (
                    any(map(lambda v, action=action: v in action.option_strings and
                        action.dest != 'help' and action.dest != 'prompt', sys.argv))
                ):
                    # Consider that if any arg is passed through CLI we want to disable prompt
                    self.prompt = False
                    break
            if self.prompt:
                # if prompt
                title(parser.prog)
                for action in parser._actions:
                    if action.dest != 'help' and action.dest != 'prompt':
                        values = ask(
                            action.dest + ": " + action.help,
                            action.type, action.default, action.required, action.choices)
                        # call the action for potential values transformer
                        action(parser, self._args, values)
            else:
                # if not help requested nor prompt requested
                self._args = parser.parse_args()

                
        return self

    @abc.abstractmethod
    def run(self, args: Optional[dict] = None) -> int:
        """Run the application.

        To load argument values please call self.load_args(args)

        :param args: arguments to use or None to load from CLI.
        :returns: return code. 0 if success.
        """
        raise NotImplementedError("Please implement the execution logic in child class")
